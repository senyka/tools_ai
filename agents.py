#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevOps Multi-Agent System - CrewAI Agents Configuration
Агенты для автоматизации DevOps задач
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool  # ✅ Правильный импорт для инструментов

# LLM imports - ✅ Стабильный импорт через community
from langchain_community.chat_models import ChatOllama

# Docker
import docker
from docker.errors import DockerException, NotFound, APIError

# Настройка логирования
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral")
LOGS_DIR = Path(os.getenv("LOGS_DIR", "/app/logs"))
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ✅ Инициализация LLM через ChatOllama (совместимо с CrewAI)
def init_llm():
    """Инициализация LLM с базовыми параметрами для устранения WARN в Ollama"""
    try:
        return ChatOllama(
            base_url=OLLAMA_HOST,
            model=MODEL_NAME,
            temperature=0.1,  # Минимальная температура для стабильности DevOps задач
        )
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise

# ✅ Глобальный LLM экземпляр
llm = init_llm()

# ✅ Инициализация Docker клиента с обработкой ошибок
def init_docker_client():
    """Безопасная инициализация Docker клиента"""
    try:
        client = docker.from_env()
        client.ping()  # Проверка соединения
        logger.info("✓ Docker client initialized")
        return client
    except DockerException as e:
        logger.warning(f"⚠ Docker not available: {e}. Running in simulation mode.")
        return None
    except Exception as e:
        logger.error(f"✗ Docker initialization error: {e}")
        return None

docker_client = init_docker_client()

def check_docker_connection() -> bool:
    """Проверить доступность Docker"""
    if docker_client is None:
        return False
    try:
        docker_client.ping()
        return True
    except:
        return False

# ==================== 🛠️ ИНСТРУМЕНТЫ (CrewAI @tool) ====================

@tool("get_docker_status")
def get_docker_status() -> str:
    """Получить статус всех контейнеров. Возвращает JSON со списком контейнеров."""
    if docker_client is None:
        return json.dumps({"error": "Docker not available", "simulation_mode": True}, indent=2)
    
    try:
        containers = docker_client.containers.list(all=True)
        status = []
        for c in containers:
            status.append({
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else c.image.short_id,
                'ports': c.ports or {},
                'created': c.attrs.get('Created', 'unknown'),
                'state': c.attrs.get('State', {}).get('Status', 'unknown')
            })
        return json.dumps(status, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting docker status: {e}")
        return json.dumps({"error": str(e)}, indent=2)

@tool("get_container_logs")
def get_container_logs(container_name: str, tail: int = 100) -> str:
    """Получить логи контейнера. Параметры: container_name (str), tail (int, default=100)."""
    if docker_client is None:
        return f"[SIMULATION] Would get last {tail} lines from '{container_name}'"
    
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=tail, stderr=True, stdout=True).decode('utf-8', errors='replace')
        return logs if logs else "[No logs available]"
    except NotFound:
        return f"Error: Container '{container_name}' not found"
    except Exception as e:
        logger.error(f"Error getting logs for {container_name}: {e}")
        return f"Error: {str(e)}"

@tool("start_container")
def start_container(container_name: str, timeout: int = 10) -> str:
    """Запустить контейнер. Параметры: container_name (str), timeout (int, seconds)."""
    if docker_client is None:
        return f"[SIMULATION] Would start container '{container_name}'"
    
    try:
        container = docker_client.containers.get(container_name)
        container.start()
        logger.info(f"Container '{container_name}' started")
        return f"✓ Container '{container_name}' started successfully"
    except NotFound:
        return f"Error: Container '{container_name}' not found"
    except Exception as e:
        logger.error(f"Error starting {container_name}: {e}")
        return f"Error: {str(e)}"

@tool("stop_container")
def stop_container(container_name: str, timeout: int = 10) -> str:
    """Остановить контейнер. Параметры: container_name (str), timeout (int, seconds)."""
    if docker_client is None:
        return f"[SIMULATION] Would stop container '{container_name}'"
    
    try:
        container = docker_client.containers.get(container_name)
        container.stop(timeout=timeout)
        logger.info(f"Container '{container_name}' stopped")
        return f"✓ Container '{container_name}' stopped successfully"
    except NotFound:
        return f"Error: Container '{container_name}' not found"
    except Exception as e:
        logger.error(f"Error stopping {container_name}: {e}")
        return f"Error: {str(e)}"

@tool("restart_container")
def restart_container(container_name: str, timeout: int = 10) -> str:
    """Перезапустить контейнер. Параметры: container_name (str), timeout (int, seconds)."""
    if docker_client is None:
        return f"[SIMULATION] Would restart container '{container_name}'"
    
    try:
        container = docker_client.containers.get(container_name)
        container.restart(timeout=timeout)
        logger.info(f"Container '{container_name}' restarted")
        return f"✓ Container '{container_name}' restarted successfully"
    except NotFound:
        return f"Error: Container '{container_name}' not found"
    except Exception as e:
        logger.error(f"Error restarting {container_name}: {e}")
        return f"Error: {str(e)}"

@tool("deploy_compose")
def deploy_compose(project_name: str, compose_content: str, dry_run: bool = True) -> str:
    """
    Развернуть Docker Compose проект.
    Параметры:
    - project_name: имя проекта
    - compose_content: содержимое docker-compose.yml
    - dry_run: если True, только валидация без реального деплоя
    """
    try:
        # Валидация базового синтаксиса
        if 'version:' not in compose_content and 'services:' not in compose_content:
            return "Error: Invalid compose format - missing 'version' or 'services'"
        
        if dry_run or docker_client is None:
            # Симуляция: сохраняем конфиг для аудита
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = LOGS_DIR / f"compose_{project_name}_{timestamp}.yml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Validated at {datetime.now().isoformat()}\n")
                f.write(f"# dry_run={dry_run}, docker_available={docker_client is not None}\n\n")
                f.write(compose_content)
            return f"✓ Compose configuration validated and saved to {filename}. {'Ready for manual review.' if dry_run else 'Deploy simulation complete.'}"
        
        # Реальный деплой (только если dry_run=False и Docker доступен)
        # ⚠️ В продакшене здесь нужен строгий аудит и sandbox
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            tmp.write(compose_content)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run(
                ['docker-compose', '-f', tmp_path, '-p', project_name, 'up', '-d', '--remove-orphans'],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Project '{project_name}' deployed successfully")
                return f"✓ Project '{project_name}' deployed successfully\n{result.stdout}"
            else:
                return f"Error deploying project: {result.stderr}"
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Error in deploy_compose: {e}")
        return f"Error: {str(e)}"

@tool("check_service_health")
def check_service_health(service_name: str, port: Optional[int] = None) -> str:
    """
    Проверить здоровье сервиса.
    Параметры: service_name (str), port (int, optional)
    """
    if docker_client is None:
        return json.dumps({
            "name": service_name,
            "status": "unknown",
            "simulation_mode": True
        }, indent=2)
    
    try:
        container = docker_client.containers.get(service_name)
        attrs = container.attrs
        state = attrs.get('State', {})
        
        health = {
            'name': service_name,
            'status': container.status,
            'running': container.status == 'running',
            'restart_count': state.get('RestartCount', 0),
            'finished_at': state.get('FinishedAt', 'N/A')
        }
        
        # Healthcheck из Docker
        if 'Health' in state:
            health['health_status'] = state['Health']['Status']
            health['health_log'] = state['Health'].get('Log', [])[-3:]  # Последние 3 проверки
        
        # Проверка порта (если указан)
        if port:
            port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            port_key = f"{port}/tcp"
            health['port_exposed'] = port_key in port_bindings
            if port_bindings.get(port_key):
                health['port_mapping'] = port_bindings[port_key]
        
        return json.dumps(health, indent=2, ensure_ascii=False)
        
    except NotFound:
        return json.dumps({"error": f"Service '{service_name}' not found"}, indent=2)
    except Exception as e:
        logger.error(f"Error checking health of {service_name}: {e}")
        return json.dumps({"error": str(e)}, indent=2)

# ✅ Список инструментов для экспорта
ALL_DOCKER_TOOLS = [
    get_docker_status,
    get_container_logs,
    start_container,
    stop_container,
    restart_container,
    deploy_compose,
    check_service_health
]

# ==================== 👥 АГЕНТЫ ====================

def create_deploy_agent():
    """Создать агента развертывания с инструментами"""
    return Agent(
        role='DevOps Deployment Engineer',
        goal='Безопасно развернуть и управлять Docker Compose проектами',
        backstory="""Ты опытный DevOps инженер с экспертизой в контейнеризации.
Ты всегда проверяешь конфигурации перед применением, соблюдаешь best practices
и минимизируешь downtime при обновлениях.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[deploy_compose, get_docker_status, check_service_health],  # ✅ Инструменты подключены
        max_iter=10
    )

def create_log_analyzer_agent():
    """Создать агента анализа логов"""
    return Agent(
        role='Senior Log Analyst',
        goal='Выявлять корневые причины проблем через анализ логов',
        backstory="""Ты эксперт по observability с 10+ лет опыта.
Ты умеешь отличать шум от реальных проблем, находишь паттерны
в логах и предлагаешь конкретные действия для исправления.""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
        tools=[get_container_logs, get_docker_status],  # ✅ Инструменты подключены
        max_iter=15
    )

def create_fix_agent():
    """Создать агента исправления ошибок"""
    return Agent(
        role='DevOps Troubleshooter',
        goal='Предлагать и применять безопасные исправления конфигураций',
        backstory="""Ты мастер root cause analysis. Ты не просто чинишь симптомы,
а находишь и устраняешь корневые причины. Ты всегда предлагаешь
минимально инвазивные исправления с откатом.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[deploy_compose, start_container, stop_container, restart_container, check_service_health],
        max_iter=12
    )

def create_monitor_agent():
    """Создать агента мониторинга"""
    return Agent(
        role='System Health Monitor',
        goal='Круглосуточно отслеживать здоровье сервисов и метрики',
        backstory="""Ты автоматизированный SRE-ассистент. Ты проактивно
обнаруживаешь аномалии, отслеживаешь SLA/SLO и генерируешь
действенные алерты без ложных срабатываний.""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
        tools=[get_docker_status, check_service_health, get_container_logs],
        max_iter=8
    )

# Кэширование агентов
_agents_cache = {}

def get_agent(name: str):
    """Получить или создать агента по имени"""
    if name not in _agents_cache:
        creators = {
            'deploy': create_deploy_agent,
            'log_analyzer': create_log_analyzer_agent,
            'fix': create_fix_agent,
            'monitor': create_monitor_agent
        }
        if name in creators:
            _agents_cache[name] = creators[name]()
        else:
            raise ValueError(f"Unknown agent: {name}")
    return _agents_cache[name]

# ==================== 📋 ЗАДАЧИ ====================

def create_deploy_task(compose_config: str, project_name: str, dry_run: bool = True) -> Task:
    return Task(
        description=f"""
Проанализируй и выполни развертывание Docker Compose проекта.

📋 Конфигурация проекта "{project_name}":
```yaml
{compose_config}
```

Действия:
1. Проверь синтаксис YAML.
2. Если dry_run=True, только провалидируй и сохрани конфиг.
3. Если dry_run=False, выполни деплой через инструмент deploy_compose.

Результат должен содержать подробный отчет о выполненных действиях.""",
        expected_output="Отчет о развертывании проекта с деталями валидации и статусом контейнеров.",
        agent=get_agent('deploy')
    )

def get_crew_instance(agents_list: List[Agent], tasks_list: List[Task]) -> Crew:
    """Создать экземпляр Crew для выполнения задач"""
    return Crew(
        agents=agents_list,
        tasks=tasks_list,
        process=Process.sequential,
        verbose=True
    )
