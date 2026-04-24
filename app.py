#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevOps Multi-Agent System API
FastAPI backend для управления агентами CrewAI
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import json
import threading
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
import logging

# Импорт агентов
from agents import get_crew_instance, docker_client, check_docker_connection

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 Starting DevOps Multi-Agent System API...")
    try:
        if check_docker_connection():
            logger.info("✓ Connected to Docker daemon")
        else:
            logger.warning("⚠ Docker connection failed - running in limited mode")
    except Exception as e:
        logger.error(f"✗ Docker initialization error: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API...")
    if docker_client:
        docker_client.close()

app = FastAPI(
    title="DevOps Multi-Agent System API",
    description="API для управления DevOps-агентами на базе CrewAI",
    version="1.1.0",
    lifespan=lifespan
)

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== THREAD-SAFE STORAGE ====================

class ThreadSafeResults:
    """Потокобезопасное хранилище результатов"""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value
            self._data['timestamp'] = datetime.now().isoformat()
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return self._data.copy()
    
    def clear(self):
        with self._lock:
            self._data.clear()

latest_results = ThreadSafeResults()

# ==================== МОДЕЛИ ДАННЫХ ====================

class ComposeDeployRequest(BaseModel):
    compose_config: str = Field(..., min_length=10, description="Содержимое docker-compose.yml")
    project_name: Optional[str] = Field(default="devops_project", max_length=100)
    dry_run: Optional[bool] = Field(default=False, description="Только проверка без деплоя")

class LogAnalysisRequest(BaseModel):
    container_names: List[str] = Field(..., min_items=1, description="Список имён контейнеров")
    tail_lines: Optional[int] = Field(default=200, ge=1, le=10000, description="Количество строк логов")
    include_errors_only: Optional[bool] = Field(default=False)

class FixRequest(BaseModel):
    error_report: str = Field(..., min_length=20, description="Отчёт об ошибках для анализа")
    auto_apply: Optional[bool] = Field(default=False, description="Автоматически применять исправления")

class ContainerActionRequest(BaseModel):
    container_name: str = Field(..., min_length=1, description="Имя контейнера")
    action: str = Field(..., pattern="^(start|stop|restart|pause|unpause)$", description="Действие")
    timeout: Optional[int] = Field(default=10, ge=1, le=300, description="Таймаут в секундах")

class APIResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

def _handle_docker_error(func):
    """Декоратор для обработки ошибок Docker"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Docker error in {func.__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"Docker operation failed: {str(e)}")
    return wrapper

# ==================== ЭНДПОИНТЫ ====================

@app.get("/", response_model=APIResponse, tags=["Root"])
def root():
    """Корневой эндпоинт"""
    return APIResponse(
        status="running",
        message="DevOps Multi-Agent System API v1.1.0",
        data={"docs": "/docs", "health": "/health"}
    )

@app.get("/health", response_model=APIResponse, tags=["Health"])
def health_check():
    """Проверка здоровья API и подключения к Docker"""
    docker_status = "disconnected"
    docker_error = None
    
    try:
        if check_docker_connection():
            docker_status = "connected"
        else:
            docker_error = "Ping failed"
    except Exception as e:
        docker_status = "error"
        docker_error = str(e)
    
    return APIResponse(
        status="healthy" if docker_status == "connected" else "degraded",
        message=f"Docker: {docker_status}",
        data={
            "api_version": "1.1.0",
            "docker_status": docker_status,
            "docker_error": docker_error,
            "uptime": datetime.now().isoformat()
        }
    )

@app.get("/containers", response_model=APIResponse, tags=["Containers"])
@_handle_docker_error
def list_containers(all_containers: bool = True):
    """Получить список всех контейнеров"""
    containers = docker_client.containers.list(all=all_containers)
    result = []
    
    for c in containers:
        # Безопасное получение тегов образа
        image_tags = c.image.tags if hasattr(c.image, 'tags') else []
        image_ref = image_tags[0] if image_tags else c.image.short_id
        
        result.append({
            'id': c.short_id,
            'name': c.name,
            'status': c.status,
            'image': image_ref,
            'ports': c.ports or {},
            'created': c.attrs.get('Created', 'unknown'),
            'labels': c.labels or {}
        })
    
    return APIResponse(
        status="success",
        message=f"Found {len(result)} containers",
        data={"containers": result, "count": len(result)}
    )

@app.get("/containers/{container_name}/logs", response_model=APIResponse, tags=["Containers"])
@_handle_docker_error
def get_logs(container_name: str, tail: int = 100):
    """Получить логи контейнера"""
    container = docker_client.containers.get(container_name)
    logs_bytes = container.logs(tail=tail, stderr=True, stdout=True)
    logs = logs_bytes.decode('utf-8', errors='replace')
    
    # ✅ ИСПРАВЛЕНО: '\n' вместо 'n'
    lines_count = len(logs.split('\n')) if logs else 0
    
    return APIResponse(
        status="success",
        message=f"Retrieved {lines_count} log lines from '{container_name}'",
        data={
            "container": container_name,
            "logs": logs,
            "lines": lines_count,
            "tail_requested": tail
        }
    )

@app.post("/containers/action", response_model=APIResponse, tags=["Containers"])
@_handle_docker_error
def container_action(request: ContainerActionRequest):
    """Выполнить действие с контейнером"""
    container = docker_client.containers.get(request.container_name)
    action = request.action
    timeout = request.timeout
    
    actions_map = {
        "start": lambda: container.start(),
        "stop": lambda: container.stop(timeout=timeout),
        "restart": lambda: container.restart(timeout=timeout),
        "pause": lambda: container.pause(),
        "unpause": lambda: container.unpause(),
    }
    
    if action not in actions_map:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    actions_map[action]()
    
    logger.info(f"Container '{request.container_name}' action '{action}' completed")
    
    return APIResponse(
        status="success",
        message=f"Container '{request.container_name}' {action}ed successfully"
    )

@app.post("/deploy", response_model=APIResponse, tags=["Deployment"])
async def deploy_compose(request: ComposeDeployRequest, background_tasks: BackgroundTasks):
    """Развернуть Docker Compose проект через агента"""
    try:
        crew = get_crew_instance()
        
        # Асинхронный запуск для долгой операции
        def run_deployment():
            return crew.run_deployment(
                request.compose_config, 
                request.project_name,
                dry_run=request.dry_run
            )
        
        if request.dry_run:
            result = run_deployment()
        else:
            # Запуск в фоне для production
            background_tasks.add_task(run_deployment)
            return APIResponse(
                status="accepted",
                message="Deployment task queued for processing",
                data={"project_name": request.project_name, "dry_run": request.dry_run}
            )
        
        return APIResponse(
            status="success",
            message=f"Deployment completed for '{request.project_name}'",
            data={
                "project_name": request.project_name,
                "result": str(result)[:500] + "..." if len(str(result)) > 500 else str(result),
                "full_result_available": "/results"
            }
        )
        
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.post("/analyze-logs", response_model=APIResponse, tags=["Analysis"])
async def analyze_logs(request: LogAnalysisRequest):
    """Анализировать логи контейнеров через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_log_analysis(
            request.container_names,
            tail_lines=request.tail_lines,
            errors_only=request.include_errors_only
        )
        
        return APIResponse(
            status="success",
            message=f"Analyzed {len(request.container_names)} containers",
            data={
                "containers_analyzed": request.container_names,
                "analysis_summary": str(result)[:300] + "...",
                "full_analysis": "/results"
            }
        )
    except Exception as e:
        logger.error(f"Log analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/fix", response_model=APIResponse, tags=["Fixes"])
async def fix_errors(request: FixRequest):
    """Исправить ошибки через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_fix_procedure(
            request.error_report, 
            auto_apply=request.auto_apply
        )
        
        return APIResponse(
            status="success",
            message="Fix procedure completed",
            data={
                "fixes_applied": str(result)[:400] + "...",
                "auto_applied": request.auto_apply,
                "full_report": "/results"
            }
        )
    except Exception as e:
        logger.error(f"Fix error: {e}")
        raise HTTPException(status_code=500, detail=f"Fix failed: {str(e)}")

@app.get("/monitor", response_model=APIResponse, tags=["Monitoring"])
async def run_monitor():
    """Запустить мониторинг системы через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_health_check()
        
        return APIResponse(
            status="success",
            message="Health check completed",
            data={"health_report": str(result)}
        )
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

@app.post("/full-cycle", response_model=APIResponse, tags=["Automation"])
async def run_full_cycle(compose_config: Optional[str] = None):
    """Запустить полный цикл: деплой -> мониторинг -> анализ -> исправление"""
    try:
        crew = get_crew_instance()
        result = crew.run_full_cycle(compose_config)
        
        # ✅ Потокобезопасное сохранение
        latest_results.set('last_cycle', result)
        
        return APIResponse(
            status="success",
            message="Full automation cycle completed",
            data={
                "stages_completed": list(result.keys()),
                "results_preview": {k: str(v)[:100] for k, v in result.items()},
                "full_results": "/results"
            }
        )
    except Exception as e:
        logger.error(f"Full cycle error: {e}")
        raise HTTPException(status_code=500, detail=f"Cycle failed: {str(e)}")

@app.get("/results", response_model=APIResponse, tags=["Results"])
def get_latest_results():
    """Получить последние результаты работы агентов"""
    data = latest_results.get_all()
    
    if not data:
        return APIResponse(
            status="no_results",
            message="No results available yet. Run an operation first."
        )
    
    return APIResponse(
        status="success",
        message=f"Results from {data.get('timestamp', 'unknown')}",
        data=data
    )

@app.delete("/results", response_model=APIResponse, tags=["Results"])
def clear_results():
    """Очистить сохранённые результаты"""
    latest_results.clear()
    return APIResponse(status="success", message="Results cleared")

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    # Создание директории для логов при запуске локально
    import os
    os.makedirs("/app/logs", exist_ok=True)
    
    logger.info("🚀 Starting DevOps Multi-Agent System API in standalone mode...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
