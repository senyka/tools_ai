from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import json
import threading
from datetime import datetime

# Импорт агентов
from agents import get_crew_instance, docker_client

app = FastAPI(title="DevOps Multi-Agent System API")

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальная переменная для хранения результатов
latest_results = {}

# ==================== МОДЕЛИ ДАННЫХ ====================

class ComposeDeployRequest(BaseModel):
    compose_config: str
    project_name: Optional[str] = "devops_project"

class LogAnalysisRequest(BaseModel):
    container_names: List[str]
    tail_lines: Optional[int] = 200

class FixRequest(BaseModel):
    error_report: str

class ContainerActionRequest(BaseModel):
    container_name: str
    action: str  # start, stop, restart

# ==================== ЭНДПОИНТЫ ====================

@app.get("/")
def root():
    return {
        "message": "DevOps Multi-Agent System API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """Проверка здоровья API и подключения к Docker"""
    try:
        docker_client.ping()
        docker_status = "connected"
    except Exception as e:
        docker_status = f"disconnected: {str(e)}"
    
    return {
        "api_status": "healthy",
        "docker_status": docker_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/containers")
def list_containers(all_containers: bool = True):
    """Получить список всех контейнеров"""
    try:
        containers = docker_client.containers.list(all=all_containers)
        result = []
        for c in containers:
            result.append({
                'id': c.id[:12],
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else c.image.short_id,
                'ports': c.ports,
                'created': str(c.created_at)
            })
        return {"containers": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/containers/{container_name}/logs")
def get_logs(container_name: str, tail: int = 100):
    """Получить логи контейнера"""
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=tail).decode('utf-8')
        return {
            "container": container_name,
            "logs": logs,
            "lines": len(logs.split('\n'))
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/containers/action")
def container_action(request: ContainerActionRequest):
    """Выполнить действие с контейнером (start/stop/restart)"""
    try:
        container = docker_client.containers.get(request.container_name)
        
        if request.action == "start":
            container.start()
            message = f"Container '{request.container_name}' started"
        elif request.action == "stop":
            container.stop()
            message = f"Container '{request.container_name}' stopped"
        elif request.action == "restart":
            container.restart()
            message = f"Container '{request.container_name}' restarted"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
        return {"status": "success", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy")
def deploy_compose(request: ComposeDeployRequest):
    """Развернуть Docker Compose проект через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_deployment(request.compose_config)
        
        return {
            "status": "success",
            "project_name": request.project_name,
            "result": str(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-logs")
def analyze_logs(request: LogAnalysisRequest):
    """Анализировать логи контейнеров через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_log_analysis(request.container_names)
        
        return {
            "status": "success",
            "containers_analyzed": request.container_names,
            "analysis": str(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fix")
def fix_errors(request: FixRequest):
    """Исправить ошибки через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_fix_procedure(request.error_report)
        
        return {
            "status": "success",
            "fixes_applied": str(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor")
def run_monitor():
    """Запустить мониторинг системы через агента"""
    try:
        crew = get_crew_instance()
        result = crew.run_health_check()
        
        return {
            "status": "success",
            "health_report": str(result),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/full-cycle")
def run_full_cycle(compose_config: Optional[str] = None):
    """Запустить полный цикл: деплой -> мониторинг -> анализ -> исправление"""
    try:
        crew = get_crew_instance()
        result = crew.run_full_cycle(compose_config)
        
        # Сохраняем результаты
        latest_results['last_cycle'] = result
        latest_results['timestamp'] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "results": {k: str(v) for k, v in result.items()},
            "timestamp": latest_results['timestamp']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
def get_latest_results():
    """Получить последние результаты работы агентов"""
    if not latest_results:
        return {"status": "no_results", "message": "No results available yet"}
    
    return latest_results

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("🚀 Starting DevOps Multi-Agent System API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
