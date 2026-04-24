#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevOps Tasks - Вынесенные задачи для переиспользования
Этот файл опционален: вся логика уже в agents.py
Оставлен для совместимости с Dockerfile и будущей модульности
"""

# Просто импортируем всё из agents.py для обратной совместимости
from agents import (
    # Инструменты
    get_docker_status,
    get_container_logs,
    start_container,
    stop_container,
    restart_container,
    deploy_compose,
    check_service_health,
    ALL_DOCKER_TOOLS,
    
    # Агенты
    create_deploy_agent,
    create_log_analyzer_agent,
    create_fix_agent,
    create_monitor_agent,
    get_agent,
    
    # Задачи
    create_deploy_task,
    create_analyze_logs_task,
    create_fix_task,
    create_monitor_task,
    
    # Оркестрация
    DevOpsCrew,
    get_crew_instance,
    
    # Утилиты
    docker_client,
    check_docker_connection,
    llm
)

# Эксплицитный экспорт
__all__ = [
    'get_docker_status',
    'get_container_logs', 
    'start_container',
    'stop_container',
    'restart_container',
    'deploy_compose',
    'check_service_health',
    'ALL_DOCKER_TOOLS',
    'create_deploy_agent',
    'create_log_analyzer_agent',
    'create_fix_agent',
    'create_monitor_agent',
    'get_agent',
    'create_deploy_task',
    'create_analyze_logs_task',
    'create_fix_task',
    'create_monitor_task',
    'DevOpsCrew',
    'get_crew_instance',
    'docker_client',
    'check_docker_connection',
    'llm'
]

# Для обратной совместимости с импортом "from tasks import *"
if __name__ == "__main__":
    print("tasks.py is a compatibility module - import from agents.py directly")
