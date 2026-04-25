import time
import docker
from agents import log_analyzer_agent, fix_agent, docker_client
from crewai import Task, Crew, Process

"""
Фоновый наблюдатель (Watcher) для автоматического мониторинга и исправления ошибок.
Запускается как отдельный сервис и постоянно отслеживает состояние контейнеров.
"""

POLL_INTERVAL = 30  # Интервал опроса в секундах
ERROR_THRESHOLD = 3  # Количество ошибок для запуска исправления

def check_container_errors(container, tail=50):
    """Проверить контейнер на наличие свежих ошибок"""
    try:
        logs = container.logs(tail=tail).decode('utf-8')
        error_keywords = ['ERROR', 'FATAL', 'CRITICAL', 'Exception', 'Traceback']
        
        errors_found = []
        for line in logs.split('\n'):
            for keyword in error_keywords:
                if keyword in line:
                    errors_found.append(line.strip())
                    break
        
        return errors_found
    except Exception as e:
        return []

def analyze_with_ai(errors, container_name):
    """Использовать ИИ-агента для анализа ошибок"""
    try:
        task = Task(
            description=f"""
            Проанализируй ошибки контейнера '{container_name}':
            
            {chr(10).join(errors)}
            
            Определи:
            1. Корневую причину проблем
            2. Критичность каждой ошибки
            3. Рекомендации по исправлению
            """,
            expected_output="Структурированный анализ ошибок с приоритетами",
            agent=log_analyzer_agent
        )
        
        crew = Crew(
            agents=[log_analyzer_agent],
            tasks=[task],
            verbose=False,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

def fix_with_ai(analysis, container_name):
    """Использовать ИИ-агента для исправления ошибок"""
    try:
        task = Task(
            description=f"""
            На основе анализа ошибок контейнера '{container_name}' примени исправления:
            
            Анализ:
            {analysis}
            
            Действия:
            1. Предложи конкретные исправления
            2. Перезапусти контейнер если необходимо
            3. Проверь что ошибки устранены
            """,
            expected_output="Отчет о примененных исправлениях",
            agent=fix_agent
        )
        
        crew = Crew(
            agents=[fix_agent],
            tasks=[task],
            verbose=False,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"AI fix failed: {str(e)}"

def get_container_stats():
    """Получить статистику по контейнерам"""
    try:
        containers = docker_client.containers.list()
        stats = {
            'total': len(containers),
            'running': 0,
            'restarting': 0,
            'errors': 0
        }
        
        for c in containers:
            if c.status == 'running':
                stats['running'] += 1
            elif c.status == 'restarting':
                stats['restarting'] += 1
            
            # Проверка на restart loop
            container_info = c.attrs
            restart_count = container_info.get('RestartCount', 0)
            if restart_count > 5:
                stats['errors'] += 1
        
        return stats
    except Exception as e:
        return {'error': str(e)}

def main_loop():
    """Основной цикл наблюдателя"""
    print("👁️  DevOps Watcher started...")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"Error threshold: {ERROR_THRESHOLD}")
    
    error_history = {}  # История ошибок по контейнерам
    
    while True:
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scanning containers...")
            
            containers = docker_client.containers.list()
            
            for container in containers:
                if container.status != 'running':
                    continue
                
                container_name = container.name
                
                # Проверка на ошибки
                errors = check_container_errors(container)
                
                if errors:
                    print(f"⚠️  Found {len(errors)} errors in {container_name}")
                    
                    # Накопление истории ошибок
                    if container_name not in error_history:
                        error_history[container_name] = []
                    
                    error_history[container_name].extend(errors)
                    
                    # Если ошибок больше порога - запуск ИИ-анализа
                    if len(error_history[container_name]) >= ERROR_THRESHOLD:
                        print(f"🤖 Threshold reached for {container_name}, running AI analysis...")
                        
                        # Анализ через ИИ
                        analysis = analyze_with_ai(
                            error_history[container_name][-10:],  # Последние 10 ошибок
                            container_name
                        )
                        print(f"📊 Analysis result:\n{analysis}")
                        
                        # Попытка исправления через ИИ
                        print("🔧 Attempting AI-powered fix...")
                        fix_result = fix_with_ai(analysis, container_name)
                        print(f"✅ Fix result:\n{fix_result}")
                        
                        # Сброс истории после попытки исправления
                        error_history[container_name] = []
                else:
                    # Сброс истории если ошибок нет
                    if container_name in error_history:
                        error_history[container_name] = []
            
            # Вывод статистики
            stats = get_container_stats()
            print(f"📈 Stats: {stats}")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 Watcher stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in watcher loop: {str(e)}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main_loop()
