import os
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama
from langchain_community.llms import Ollama
import docker
import json
from datetime import datetime

# Конфигурация
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral")

# Инициализация LLM через OpenAI-compatible API Ollama
llm = ChatOllama(
    base_url=OLLAMA_HOST,
    model=MODEL_NAME,
    temperature=0.7
)

# Инициализация Docker клиента
docker_client = docker.from_env()

# ==================== АГЕНТЫ ====================

# 1. Агент развертывания (Deployment Agent)
deploy_agent = Agent(
    role='DevOps Deployment Engineer',
    goal='Развернуть Docker Compose проекты и управлять контейнерами',
    backstory="""Ты опытный DevOps инженер, специализирующийся на автоматизации развертывания.
    Твоя задача - корректно запускать, останавливать и перезапускать контейнеры.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[]  # Инструменты будут добавлены через функции
)

# 2. Агент анализа логов (Log Analyzer Agent)
log_analyzer_agent = Agent(
    role='Senior Log Analyst',
    goal='Анализировать логи контейнеров, выявлять ошибки и аномалии',
    backstory="""Ты эксперт по анализу логов с многолетним опытом.
    Ты умеешь находить корневые причины проблем по логам и предлагать решения.""",
    verbose=True,
    allow_delegation=True,
    llm=llm
)

# 3. Агент исправления ошибок (Fix Agent)
fix_agent = Agent(
    role='DevOps Troubleshooter',
    goal='Исправлять ошибки в конфигурациях Docker и кодах приложений',
    backstory="""Ты мастер решения проблем. Ты анализируешь ошибки и предлагаешь конкретные исправления.
    Ты умеешь модифицировать docker-compose.yml, Dockerfile и конфигурационные файлы.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 4. Агент мониторинга (Monitoring Agent)
monitor_agent = Agent(
    role='System Health Monitor',
    goal='Контролировать работоспособность сервисов и метрики производительности',
    backstory="""Ты круглосуточный монитор систем. Ты отслеживаешь статус контейнеров, 
    использование ресурсов и доступность сервисов.""",
    verbose=True,
    allow_delegation=True,
    llm=llm
)

# ==================== ИНСТРУМЕНТЫ ====================

def get_docker_status():
    """Получить статус всех контейнеров"""
    try:
        containers = docker_client.containers.list(all=True)
        status = []
        for c in containers:
            status.append({
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else c.image.id[:12],
                'ports': c.ports,
                'created': str(c.created_at)
            })
        return json.dumps(status, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

def get_container_logs(container_name, tail=100):
    """Получить логи конкретного контейнера"""
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=tail).decode('utf-8')
        return logs
    except docker.errors.NotFound:
        return f"Container '{container_name}' not found"
    except Exception as e:
        return f"Error: {str(e)}"

def start_container(container_name):
    """Запустить контейнер"""
    try:
        container = docker_client.containers.get(container_name)
        container.start()
        return f"Container '{container_name}' started successfully"
    except Exception as e:
        return f"Error starting container: {str(e)}"

def stop_container(container_name):
    """Остановить контейнер"""
    try:
        container = docker_client.containers.get(container_name)
        container.stop()
        return f"Container '{container_name}' stopped successfully"
    except Exception as e:
        return f"Error stopping container: {str(e)}"

def restart_container(container_name):
    """Перезапустить контейнер"""
    try:
        container = docker_client.containers.get(container_name)
        container.restart()
        return f"Container '{container_name}' restarted successfully"
    except Exception as e:
        return f"Error restarting container: {str(e)}"

def deploy_compose(project_name, compose_content):
    """Развернуть Docker Compose проект (симуляция через запись файла)"""
    try:
        # В реальном сценарии здесь был бы вызов docker-compose up
        # Для безопасности записываем конфиг в файл для проверки
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/logs/compose_{project_name}_{timestamp}.yml"
        with open(filename, 'w') as f:
            f.write(compose_content)
        return f"Compose configuration saved to {filename}. Ready for deployment review."
    except Exception as e:
        return f"Error deploying compose: {str(e)}"

def check_service_health(service_name, port=None):
    """Проверить здоровье сервиса"""
    try:
        container = docker_client.containers.get(service_name)
        health = {
            'name': service_name,
            'status': container.status,
            'running': container.status == 'running'
        }
        
        if container.attrs.get('State', {}).get('Health'):
            health['health_status'] = container.attrs['State']['Health']['Status']
        
        return json.dumps(health, indent=2)
    except docker.errors.NotFound:
        return f"Service '{service_name}' not found"
    except Exception as e:
        return f"Error checking health: {str(e)}"

# Экспорт инструментов для использования в app.py
DOCKER_TOOLS = [
    get_docker_status,
    get_container_logs,
    start_container,
    stop_container,
    restart_container,
    deploy_compose,
    check_service_health
]

# ==================== ЗАДАЧИ ====================

def create_deploy_task(compose_config):
    return Task(
        description=f"""
        Проанализируй конфигурацию Docker Compose и выполни развертывание:
        
        Конфигурация:
        {compose_config}
        
        Шаги:
        1. Проверь синтаксис и валидность конфигурации
        2. Определи необходимые образы и их версии
        3. Проверь конфликты портов
        4. Разверни сервисы в правильном порядке
        5. Убедись, что все контейнеры запущены
        
        Верни подробный отчет о процессе развертывания.
        """,
        expected_output="Отчет о развертывании со статусом каждого сервиса",
        agent=deploy_agent
    )

def create_analyze_logs_task(container_names):
    return Task(
        description=f"""
        Проанализируй логи указанных контейнеров на наличие ошибок:
        
        Контейнеры: {', '.join(container_names)}
        
        Задачи:
        1. Получи последние 200 строк логов каждого контейнера
        2. Найди ошибки (ERROR, FATAL, CRITICAL, Exception)
        3. Выяви предупреждения (WARNING, WARN)
        4. Определи паттерны повторяющихся ошибок
        5. Предложи гипотезы о причинах проблем
        
        Верни структурированный анализ с приоритетами проблем.
        """,
        expected_output="Структурированный отчет об ошибках с рекомендациями",
        agent=log_analyzer_agent
    )

def create_fix_task(error_report):
    return Task(
        description=f"""
        На основе отчета об ошибках предложи и примени исправления:
        
        Отчет об ошибках:
        {error_report}
        
        Действия:
        1. Определи корневую причину каждой критической ошибки
        2. Предложи конкретные исправления (изменение конфига, перезапуск, обновление образа)
        3. Если требуется - создай исправленную версию docker-compose.yml
        4. Примени исправления, которые можно выполнить безопасно
        5. Перезапусти затронутые сервисы
        
        Верни отчет о примененных исправлениях и результатах.
        """,
        expected_output="Отчет о примененных исправлениях и текущем статусе системы",
        agent=fix_agent
    )

def create_monitor_task():
    return Task(
        description="""
        Проведи полную проверку здоровья системы:
        
        1. Получи статус всех контейнеров
        2. Проверь использование ресурсов (CPU, память) для каждого сервиса
        3. Проверь доступность портов
        4. Выяви сервисы в состоянии restart loop или error
        5. Проверь логи на свежие ошибки (последние 50 строк)
        
        Верни дашборд состояния системы с оценкой здоровья (0-100%).
        """,
        expected_output="Дашборд состояния системы с метриками и рекомендациями",
        agent=monitor_agent
    )

# ==================== ОРКЕСТРАЦИЯ ====================

class DevOpsCrew:
    def __init__(self):
        self.crew = None
    
    def run_deployment(self, compose_config):
        """Запустить процесс развертывания"""
        task = create_deploy_task(compose_config)
        crew = Crew(
            agents=[deploy_agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        result = crew.kickoff()
        return result
    
    def run_log_analysis(self, container_names):
        """Запустить анализ логов"""
        task = create_analyze_logs_task(container_names)
        crew = Crew(
            agents=[log_analyzer_agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        result = crew.kickoff()
        return result
    
    def run_fix_procedure(self, error_report):
        """Запустить процедуру исправления"""
        task = create_fix_task(error_report)
        crew = Crew(
            agents=[fix_agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        result = crew.kickoff()
        return result
    
    def run_health_check(self):
        """Запустить проверку здоровья"""
        task = create_monitor_task()
        crew = Crew(
            agents=[monitor_agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        result = crew.kickoff()
        return result
    
    def run_full_cycle(self, compose_config=None):
        """Запустить полный цикл: деплой -> мониторинг -> анализ -> исправление"""
        results = {}
        
        # Этап 1: Развертывание
        if compose_config:
            print("🚀 Этап 1: Развертывание...")
            results['deployment'] = self.run_deployment(compose_config)
        
        # Этап 2: Мониторинг
        print("📊 Этап 2: Мониторинг...")
        results['health_check'] = self.run_health_check()
        
        # Этап 3: Анализ логов
        print("🔍 Этап 3: Анализ логов...")
        try:
            containers = docker_client.containers.list()
            container_names = [c.name for c in containers]
            if container_names:
                results['log_analysis'] = self.run_log_analysis(container_names)
        except Exception as e:
            results['log_analysis'] = f"Error getting containers: {str(e)}"
        
        # Этап 4: Исправление (если найдены ошибки)
        if 'log_analysis' in results and 'ERROR' in str(results['log_analysis']):
            print("🔧 Этап 4: Исправление ошибок...")
            results['fixes'] = self.run_fix_procedure(results['log_analysis'])
        
        return results

# Экспорт для app.py
def get_crew_instance():
    return DevOpsCrew()

if __name__ == "__main__":
    # Тестовый запуск
    print("DevOps Multi-Agent System initialized")
    print(f"Connected to Ollama at: {OLLAMA_HOST}")
    print(f"Model: {MODEL_NAME}")
    
    # Проверка подключения к Docker
    try:
        docker_client.ping()
        print("✓ Connected to Docker daemon")
    except Exception as e:
        print(f"✗ Docker connection failed: {e}")
