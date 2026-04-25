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
import os
import logging

# Импорт агентов
from agents import get_crew_instance, docker_client, check_docker_connection, get_agent, create_deploy_task

# Настройка логирования
LOGS_DIR = os.getenv("LOGS_DIR", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'api.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== МОДЕЛИ ДАННЫХ ====================

class APIResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None

class ComposeDeployRequest(BaseModel):
    compose_config: str = Field(..., min_length=10)
    project_name: Optional[str] = Field(default="devops_project")
    dry_run: Optional[bool] = Field(default=False)

class LogAnalysisRequest(BaseModel):
    container_names: List[str] = Field(..., min_items=1)
    tail_lines: Optional[int] = Field(default=200)

class ContainerActionRequest(BaseModel):
    container_name: str
    action: str = Field(..., pattern="^(start|stop|restart|pause|unpause)$")
    timeout: Optional[int] = Field(default=10)

# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
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

# ==================== HELPER FUNCTIONS ====================

def _handle_docker_error(func):
    """Декоратор для обработки ошибок Docker"""
    def wrapper(*args, **kwargs):
        if docker_client is None:
            logger.error(f"Docker client is not initialized. Cannot execute {func.__name__}")
            raise HTTPException(status_code=503, detail="Docker service unavailable or not connected")
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
    docker_status = "connected" if check_docker_connection() else "disconnected"
    return APIResponse(
        status="healthy" if docker_status == "connected" else "degraded",
        message=f"Docker: {docker_status}",
        data={
            "api_version": "1.1.0",
            "docker_status": docker_status,
            "uptime": datetime.now().isoformat()
        }
    )

@app.get("/containers", response_model=APIResponse, tags=["Containers"])
@_handle_docker_error
def list_containers(all: bool = True):
    """Получить список всех контейнеров"""
    containers = docker_client.containers.list(all=all)
    result = []
    for c in containers:
        image_tags = c.image.tags if hasattr(c.image, 'tags') else []
        image_ref = image_tags[0] if image_tags else c.image.short_id
        result.append({
            'id': c.short_id,
            'name': c.name,
            'status': c.status,
            'image': image_ref,
            'ports': c.ports or {},
            'created': c.attrs.get('Created', 'unknown')
        })
    return APIResponse(status="success", data={"containers": result, "count": len(result)})

@app.post("/deploy", response_model=APIResponse, tags=["Deployment"])
async def deploy_project(request: ComposeDeployRequest):
    """Запуск агента для деплоя проекта"""
    try:
        agent = get_agent('deploy')
        task = create_deploy_task(request.compose_config, request.project_name, request.dry_run)
        crew = get_crew_instance([agent], [task])
        result = await asyncio.to_thread(crew.kickoff)
        return APIResponse(status="success", data={"result": str(result)})
    except Exception as e:
        logger.error(f"Deploy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-logs", response_model=APIResponse, tags=["Analysis"])
async def analyze_logs(request: LogAnalysisRequest):
    """Запуск агента для анализа логов"""
    try:
        from crewai import Task
        agent = get_agent('log_analyzer')
        task = Task(
            description=f"Проанализируй логи контейнеров: {', '.join(request.container_names)}. Tail: {request.tail_lines}",
            expected_output="Технический отчет с выявленными ошибками и рекомендациями.",
            agent=agent
        )
        crew = get_crew_instance([agent], [task])
        result = await asyncio.to_thread(crew.kickoff)
        return APIResponse(status="success", data={"analysis": str(result)})
    except Exception as e:
        logger.error(f"Log analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor", response_model=APIResponse, tags=["Monitoring"])
async def run_monitoring():
    """Запуск агента мониторинга"""
    try:
        from crewai import Task
        agent = get_agent('monitor')
        task = Task(
            description="Проверь состояние всех сервисов в Docker и найди аномалии или ошибки в логах.",
            expected_output="Отчет о здоровье системы с рекомендациями по исправлению.",
            agent=agent
        )
        crew = get_crew_instance([agent], [task])
        result = await asyncio.to_thread(crew.kickoff)
        return APIResponse(status="success", data={"health_report": str(result)})
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8800)
