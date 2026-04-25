# 🤖 DevOps Multi-Agent System

Локальная мульти-агентная система для автоматизации DevOps задач на базе **CrewAI + Ollama + docker-py** с веб-интерфейсом.

## 🎯 Возможности

Система автоматически:
- ✅ **Разворачивает Docker Compose проекты** - анализ конфигурации и деплой через ИИ-агента
- 📊 **Анализирует логи контейнеров** - поиск ошибок (ERROR, FATAL, CRITICAL), аномалий и паттернов
- 🔧 **Исправляет ошибки** - автоматическое применение исправлений через ИИ-агента
- 📈 **Мониторит работоспособность 24/7** - фоновый Watcher сервис проверяет здоровье сервисов
- 🌐 **Веб-интерфейс** - управление через Streamlit dashboard (5 вкладок)
- 📡 **REST API** - 10 endpoints для интеграции и автоматизации

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Streamlit)                       │
│                      Port: 8501                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼──────────────────────────────────────┐
│              Backend API (FastAPI)                          │
│                      Port: 8000                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           CrewAI Multi-Agent System                  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │
│  │  │ Deployment  │ │   Log       │ │    Fix      │     │   │
│  │  │   Agent     │ │  Analyzer   │ │   Agent     │     │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘     │   │
│  │  ┌─────────────┐ ┌─────────────┐                     │   │
│  │  │ Monitoring  │ │  Watcher    │                     │   │
│  │  │   Agent     │ │  (Background)                      │   │
│  │  └─────────────┘ └─────────────┘                     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Docker Socket + Ollama API
┌──────────────────────▼──────────────────────────────────────┐
│  Ollama (LLM)        │        Docker Daemon                │
│  Port: 11434         │        /var/run/docker.sock         │
│  Model: mistral      │        Containers                   │
└──────────────────────┴──────────────────────────────────────┘
```

## 📁 Структура проекта

```
/workspace
├── docker-compose.yml       # Основная конфигурация (4 сервиса: ollama, crewai_backend, web_ui, watcher)
├── Dockerfile.backend       # Dockerfile для backend с агентами CrewAI
├── Dockerfile.ui            # Dockerfile для веб-интерфейса Streamlit
├── requirements.txt         # Python зависимости (crewai, langchain, fastapi, streamlit, docker-py)
├── agents.py                # 4 ИИ-агента: Deployment, LogAnalyzer, Fix, Monitoring + DevOpsCrew класс
├── app.py                   # FastAPI backend приложение (10 REST endpoints)
├── web_ui.py                # Streamlit веб-интерфейс (5 вкладок: Dashboard, Deploy, Logs, Fix, Manage)
├── watcher.py               # Фоновый наблюдатель для авто-мониторинга и исправлений
└── README.md                # Документация
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Минимум 8GB RAM (рекомендуется 16GB)
- 20GB свободного места на диске

### Установка и запуск

```bash
# 1. Перейдите в директорию проекта
cd /workspace

# 2. Загрузите модель Ollama (mistral) - выполнится автоматически при первом старте
# или предварительно:
docker run --rm ollama/ollama ollama pull mistral

# 3. Запустите всю систему (4 сервиса)
docker-compose up -d

# 4. Проверьте статус всех сервисов
docker-compose ps

# 5. Откройте веб-интерфейс
# http://localhost:8501

# 6. Проверьте API
curl http://localhost:8000/health
```

### Остановка системы

```bash
docker-compose down
# или с удалением данных
docker-compose down -v
```

## 🎭 ИИ-Агенты

Система использует 4 специализированных агента на базе CrewAI + Ollama (mistral):

### 1. 🚀 Deployment Agent
**Роль:** DevOps Deployment Engineer  
**Задачи:**
- Анализ конфигураций Docker Compose перед развертыванием
- Развертывание сервисов в правильном порядке зависимостей
- Проверка конфликтов портов и ресурсов
- Управление жизненным циклом контейнеров (start/stop/restart)
- Сохранение истории деплоев в `/app/logs`

### 2. 📊 Log Analyzer Agent
**Роль:** Senior Log Analyst  
**Задачи:**
- Анализ логов на наличие ошибок (ERROR, FATAL, CRITICAL, Exception, Traceback)
- Выявление паттернов и аномалий в поведении сервисов
- Определение корневых причин проблем (root cause analysis)
- Приоритизация проблем по критичности (High/Medium/Low)
- Формирование структурированных отчетов с рекомендациями

### 3. 🔧 Fix Agent
**Роль:** DevOps Troubleshooter  
**Задачи:**
- Автоматическое исправление конфигураций docker-compose.yml
- Перезапуск проблемных сервисов с применением исправлений
- Генерация исправленных версий конфигов
- Валидация примененных исправлений через повторный мониторинг
- Ведение лога всех внесенных изменений

### 4. 📈 Monitoring Agent
**Роль:** System Health Monitor  
**Задачи:**
- Постоянный мониторинг статуса контейнеров (running/stopped/error)
- Проверка использования ресурсов (CPU, memory)
- Обнаружение restart loop и других аномалий
- Формирование дашборда здоровья системы (0-100%)
- Интеграция с Watcher для автоматических алертов

## 🌐 Веб-интерфейс

Веб-интерфейс доступен по адресу **http://localhost:8501** и включает 5 вкладок:

### 📊 Дашборд
- Статус всех контейнеров в реальном времени (running/stopped/error)
- Метрики: всего/запущено/остановлено/с ошибками
- Таблица контейнеров с деталями (имя, статус, IP, порты)
- Результаты последнего мониторинга от ИИ-агентов
- Индикатор общего здоровья системы (%)

### 🚀 Развертывание
- Редактор Docker Compose конфигураций с подсветкой YAML
- Валидация синтаксиса перед отправкой агенту
- Деплой через ИИ-агента Deployment Agent
- Отчет о процессе развертывания с этапами
- История деплоев с временными метками

### 📝 Логи
- Выбор одного или нескольких контейнеров для анализа
- Просмотр логов в реальном времени с автообновлением
- Фильтрация по уровню (ERROR, WARN, INFO)
- ИИ-анализ ошибок с рекомендациями от Log Analyzer Agent
- Экспорт отчетов в JSON/TXT

### 🔧 Исправление
- Автоматическое исправление найденных ошибок через Fix Agent
- Использование контекста из предыдущего анализа логов
- Предпросмотр изменений перед применением
- Отчет о примененных изменениях с rollback информацией
- Лог всех действий агента

### ⚙️ Управление
- Старт/стоп/рестарт отдельных контейнеров
- Детальная информация о контейнере (JSON view)
- Быстрые действия через боковую панель
- Массовые операции (restart all, stop stopped)
- Перезапуск сервисов системы

## 📡 API Endpoints

Backend API доступен по адресу **http://localhost:8000** (FastAPI с автодокументацией Swagger UI на `/docs`)

| Метод | Endpoint | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/` | Статус API и версия | - |
| GET | `/health` | Проверка здоровья всех сервисов | - |
| GET | `/containers` | Список всех контейнеров | - |
| GET | `/containers/{name}/logs` | Логи конкретного контейнера | `tail` (int) |
| POST | `/containers/action` | Действие над контейнером | `container_name`, `action` (start/stop/restart) |
| POST | `/deploy` | Развернуть Compose проект через ИИ | `compose_config`, `project_name` |
| POST | `/analyze-logs` | Анализ логов через Log Analyzer Agent | `container_names[]`, `tail_lines` |
| POST | `/fix` | Исправление ошибок через Fix Agent | `log_analysis`, `container_name` |
| GET | `/monitor` | Запуск мониторинга через Monitoring Agent | - |
| POST | `/full-cycle` | Полный цикл (деплой→мониторинг→анализ→фикс) | `compose_config` (опционально) |
| GET | `/results` | Последние результаты работы агентов | - |

### Примеры использования API

```bash
# 1. Получить список контейнеров
curl http://localhost:8000/containers | jq .

# 2. Развернуть Docker Compose проект через ИИ-агента
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "compose_config": "version: \"3.8\"\nservices:\n  web:\n    image: nginx:latest\n    ports:\n      - \"8080:80\"",
    "project_name": "my_web_project"
  }' | jq .

# 3. Проанализировать логи контейнеров через Log Analyzer Agent
curl -X POST http://localhost:8000/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{
    "container_names": ["devops_ollama", "devops_crew"],
    "tail_lines": 200
  }' | jq .

# 4. Исправить найденные ошибки через Fix Agent
curl -X POST http://localhost:8000/fix \
  -H "Content-Type: application/json" \
  -d '{
    "log_analysis": "ERROR: port already in use",
    "container_name": "my_web_project_web"
  }' | jq .

# 5. Запустить мониторинг системы
curl http://localhost:8000/monitor | jq .

# 6. Запустить полный цикл (деплой → мониторинг → анализ → фикс)
curl -X POST http://localhost:8000/full-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "compose_config": "version: \"3.8\"\nservices:\n  app:\n    image: redis:alpine"
  }' | jq .

# 7. Получить последние результаты работы агентов
curl http://localhost:8000/results | jq .

# 8. Перезапустить контейнер
curl -X POST http://localhost:8000/containers/action \
  -H "Content-Type: application/json" \
  -d '{
    "container_name": "devops_ollama",
    "action": "restart"
  }' | jq .
```

**Swagger UI:** Откройте `http://localhost:8000/docs` для интерактивной документации API.

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `OLLAMA_HOST` | `http://ollama:11434` | Адрес Ollama сервера |
| `MODEL_NAME` | `mistral` | Модель LLM для агентов |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

### Настройка модели Ollama

По умолчанию используется модель `mistral`. Для использования другой модели:

```bash
# Внутри контейнера Ollama
docker exec -it devops_ollama ollama pull llama2
docker exec -it devops_ollama ollama pull codellama

# Обновите MODEL_NAME в docker-compose.yml
```

Рекомендуемые модели для DevOps задач:
- `mistral` - баланс скорости и качества (по умолчанию)
- `codellama` - лучше для работы с кодом и конфигами
- `llama2:13b` - более точные ответы, но медленнее

## 🔍 Фоновый наблюдатель (Watcher)

Сервис `watcher` работает в фоне как отдельный Docker контейнер и автоматически:

1. **Опрашивает все контейнеры** каждые 30 секунд (настраивается через `POLL_INTERVAL`)
2. **Ищет ошибки** в логах по ключевым словам: ERROR, FATAL, CRITICAL, Exception, Traceback
3. **Накопляет историю** ошибок по каждому контейнеру в памяти
4. **Запускает ИИ-анализ** при достижении порога (3 ошибки по умолчанию)
5. **Применяет исправления** через Fix Agent с ведением лога действий
6. **Сбрасывает историю** после успешного исправления или если ошибок нет

### Архитектура работы Watcher

```
┌──────────────┐     30 sec      ┌─────────────────┐
│   Containers │ ◄────────────── │    Watcher      │
└──────┬───────┘                 │   Service       │
       │ logs                    └──────┬──────────┘
       ▼                                │
┌──────────────┐                 If errors >= 3
│ Error Check  │ ──────────────────────►│
└──────────────┘                        ▼
                               ┌─────────────────┐
                               │ Log Analyzer    │
                               │ Agent (AI)      │
                               └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │ Fix Agent (AI)  │
                               │ Apply Fixes     │
                               └─────────────────┘
```

### Настройка Watcher

Параметры настраиваются в файле `watcher.py`:

```python
POLL_INTERVAL = 30      # Интервал опроса (секунды)
ERROR_THRESHOLD = 3     # Порог ошибок для запуска ИИ-агентов
```

Для изменения параметров отредактируйте файл и пересоздайте контейнер:
```bash
docker-compose up -d --force-recreate watcher
```

### Логирование Watcher

```bash
# Просмотр логов в реальном времени
docker logs devops_watcher -f

# Последние 100 строк
docker logs devops_watcher --tail 100
```

## 📊 Логирование

Логи системы сохраняются в директорию `/workspace/logs`:

```
logs/
├── compose_my_project_20240101_120000.yml  # Сохраненные конфиги деплоев
├── agent_logs_20240101.log                 # Логи работы ИИ-агентов
└── watcher_20240101.log                    # Логи наблюдателя (ошибки, исправления)
```

### Просмотр логов компонентов

```bash
# Логи backend с агентами CrewAI
docker logs devops_crew -f --tail 100

# Логи веб-интерфейса Streamlit
docker logs devops_ui -f --tail 100

# Логи наблюдателя Watcher
docker logs devops_watcher -f --tail 100

# Логи Ollama (LLM сервер)
docker logs devops_ollama -f --tail 100

# Логи конкретного контейнера через API
curl http://localhost:8000/containers/devops_crew/logs?tail=50
```

### Экспорт логов

```bash
# Сохранить логи всех сервисов в файл
docker-compose logs > all_logs.txt

# Логи только backend за последние 10 минут
docker logs devops_crew --since 10m > backend_logs.txt
```

## 🛡️ Безопасность

### ⚠️ Важные замечания

**Docker Socket Access**: Система имеет полный доступ к `/var/run/docker.sock` хоста, что дает возможность:
- Создавать/удалять любые контейнеры
- Читать логи всех сервисов
- Изменять сеть и volumes
- Получать потенциальный доступ к хост-системе

**Используйте только в доверенной среде!** Не запускайте в production без дополнительной изоляции.

**Авто-исправления**: Watcher может автоматически:
- Перезапускать контейнеры без подтверждения
- Применять исправления конфигов
- Останавливать проблемные сервисы

Для отключения авто-фикса закомментируйте сервис `watcher` в `docker-compose.yml`:
```yaml
# watcher:
#   build: ...
```

### 🔒 Рекомендации для production

1. **Изоляция сети**: Запускайте систему в отдельной Docker network без доступа к интернету
   ```yaml
   networks:
     devops_net:
       driver: bridge
       internal: true  # Без доступа вовне
   ```

2. **Ограничение прав Docker socket**: Используйте docker-socket-proxy для read-only доступа где возможно
   ```bash
   docker run -d --name socket-proxy \
     -v /var/run/docker.sock:/var/run/docker.sock:ro \
     tecnativa/docker-socket-proxy
   ```

3. **Аутентификация API**: Добавьте middleware в `app.py`:
   ```python
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   security = HTTPBearer()
   
   @app.get("/protected")
   async def protected(credentials: HTTPAuthorizationCredentials = Depends(security)):
       if credentials.credentials != os.getenv("API_TOKEN"):
           raise HTTPException(status_code=401)
   ```

4. **Rate Limiting**: Ограничьте частоту запросов к API
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

5. **Логирование действий**: Включите аудит всех действий агентов
   ```bash
   docker logs devops_crew > audit.log 2>&1
   ```

6. **Resource Limits**: Ограничьте ресурсы контейнеров
   ```yaml
   services:
     crewai_backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

## 🧪 Тестирование

### ✅ Проверка работы системы

```bash
# 1. Проверьте что все 4 сервиса запущены
docker-compose ps
# Ожидаемый статус: Up (healthy) для ollama, Up для остальных

# 2. Проверьте подключение к Ollama
curl http://localhost:11434/api/tags
# Должен вернуть список моделей

# 3. Проверьте API backend
curl http://localhost:8000/health
# {"status": "healthy", "services": {...}}

# 4. Создайте тестовый контейнер
docker run -d --name test_nginx nginx:latest

# 5. Запустите мониторинг через API
curl http://localhost:8000/monitor | jq .

# 6. Проверьте что агент видит тестовый контейнер
curl http://localhost:8000/containers | jq '.[] | select(.name | contains("test_nginx"))'

# 7. Очистите тестовый контейнер
docker rm -f test_nginx
```

### 🔬 Сценарий тестирования полного цикла

```bash
# 1. Создайте проблемный контейнер с постоянными ошибками
docker run -d --name broken_app alpine sh -c \
  "while true; do echo 'ERROR: Connection failed to database'; sleep 2; done"

# 2. Подождите накопления ошибок (30-60 секунд)
sleep 45

# 3. Запустите анализ логов через ИИ-агента
curl -X POST http://localhost:8000/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{"container_names": ["broken_app"]}' | jq .

# 4. Проверьте результаты анализа
curl http://localhost:8000/results | jq '.log_analysis'

# 5. Запустите полный цикл исправления
curl -X POST http://localhost:8000/full-cycle | jq .

# 6. Проверьте логи Watcher
docker logs devops_watcher --tail 50

# 7. Очистите тестовый контейнер
docker rm -f broken_app
```

### 📋 Чеклист успешного развертывания

- [ ] Все 4 сервиса в статусе `Up` (`docker-compose ps`)
- [ ] Ollama отвечает на `/api/tags`
- [ ] Backend API возвращает `{\"status\": \"healthy\"}`
- [ ] Веб-интерфейс открывается на http://localhost:8501
- [ ] Агенты видят контейнеры хоста
- [ ] Watcher обнаруживает ошибки в логах
- [ ] Логи сохраняются в `/workspace/logs`

## 🔧 Расширение функциональности

### Добавление новых агентов

В файле `agents.py` добавьте нового агента в секцию `# ==================== АГЕНТЫ ====================`:

```python
# Новый агент (например, Security Scanner)
security_agent = Agent(
    role='DevSecOps Security Scanner',
    goal='Анализировать конфигурации на уязвимости безопасности',
    backstory="""Ты эксперт по безопасности Docker контейнеров.
    Твоя задача - находить уязвимости в конфигурациях и образах.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Добавьте агента в класс DevOpsCrew
class DevOpsCrew:
    def __init__(self):
        self.agents = [
            deploy_agent,
            log_analyzer_agent,
            fix_agent,
            monitoring_agent,
            security_agent  # Новый агент
        ]
```

### Добавление новых инструментов (Tools)

```python
from crewai import tool

@tool
def scan_vulnerabilities(image_name: str) -> str:
    """Сканирует Docker образ на известные уязвимости"""
    import subprocess
    result = subprocess.run(
        ['docker', 'scan', image_name],
        capture_output=True, text=True
    )
    return result.stdout

# Добавьте инструмент в список DOCKER_TOOLS
DOCKER_TOOLS.append(scan_vulnerabilities)
```

### Интеграция с другими системами

Система легко расширяется для интеграции с:

| Система | Библиотека | Пример использования |
|---------|------------|---------------------|
| **Kubernetes** | `kubernetes-python` | Управление k8s кластерами через агентов |
| **Prometheus/Grafana** | `prometheus-api-client` | Сбор метрик для Monitoring Agent |
| **Slack** | `slack-sdk` | Уведомления об ошибках в каналы |
| **Telegram** | `python-telegram-bot` | Бот для управления через сообщения |
| **GitLab CI** | `python-gitlab` | Триггер пайплайнов при деплое |
| **GitHub Actions** | `PyGithub` | Создание issues при критических ошибках |
| **Elasticsearch** | `elasticsearch-py` | Централизованное логирование |
| **HashiCorp Vault** | `hvac` | Безопасное хранение секретов |

Пример интеграции с Telegram:
```python
# В agents.py добавьте инструмент
@tool
def send_telegram_message(message: str) -> str:
    """Отправляет уведомление в Telegram"""
    import requests
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    requests.post(url, json={'chat_id': chat_id, 'text': message})
    return 'Message sent'
```

## 📈 Производительность

### Требования к ресурсам

| Компонент | RAM | CPU | Disk | Примечание |
|-----------|-----|-----|------|------------|
| **Ollama (mistral)** | 4-8 GB | 2 cores | 5 GB | Зависит от модели |
| **Backend + Agents** | 2-4 GB | 1-2 cores | 2 GB | CrewAI + FastAPI |
| **Web UI** | 500 MB | 0.5 cores | 500 MB | Streamlit |
| **Watcher** | 200 MB | 0.25 cores | 100 MB | Фоновый сервис |
| **Итого** | **~8-16 GB** | **4-5 cores** | **~10 GB** | Минимальные требования |

### Оптимизация производительности

#### 1. Используйте меньшие модели для быстрых задач

```bash
# Внутри контейнера Ollama или на хосте
docker exec -it devops_ollama ollama pull mistral:7b-instruct-q4_0
docker exec -it devops_ollama ollama pull phi3:mini  # Очень быстрая модель
```

Обновите `MODEL_NAME` в `docker-compose.yml`:
```yaml
environment:
  - MODEL_NAME=mistral:7b-instruct-q4_0  # Квантованная версия (быстрее)
```

#### 2. Настройте кэширование ответов агентов

Добавьте в `agents.py`:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_llm_call(prompt: str) -> str:
    return llm.invoke(prompt).content
```

#### 3. Увеличьте интервал опроса Watcher в production

В `watcher.py`:
```python
POLL_INTERVAL = 60      # Вместо 30 секунд для production
ERROR_THRESHOLD = 5     # Вместо 3 для менее частых алертов
```

#### 4. Используйте GPU если доступно

Добавьте в `docker-compose.yml` для сервиса `ollama`:
```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # Или для AMD:
    # devices:
    #   - /dev/kfd:/dev/kfd
    #   - /dev/dri:/dev/dri
```

#### 5. Настройте параллелизм агентов

В `agents.py` измените процесс выполнения:
```python
crew = Crew(
    agents=self.agents,
    tasks=tasks,
    process=Process.hierarchical,  # Параллельное выполнение
    manager_llm=llm
)
```

#### 6. Мониторинг ресурсов системы

```bash
# Статистика использования ресурсов контейнерами
docker stats devops_ollama devops_crew devops_ui devops_watcher

# Проверка доступной памяти на хосте
free -h

# Проверка загрузки CPU
htop
```

## ❓ FAQ

### Q: Агенты работают медленно?
**A:** Это нормально для локальных LLM. Для ускорения:
- Используйте меньшую модель (`mistral:7b-instruct-q4_0` или `phi3:mini`)
- Уменьшите `temperature` в настройках LLM (быстрее генерация)
- Добавьте GPU поддержку (NVIDIA/AMD)
- Включите кэширование ответов

### Q: Как сменить модель LLM?
**A:** Измените `MODEL_NAME` в `docker-compose.yml` и пересоздайте контейнеры:
```bash
# 1. Остановите систему
docker-compose down

# 2. Измените MODEL_NAME в docker-compose.yml
# Например: MODEL_NAME=llama3:8b-instruct-q4_0

# 3. Запустите заново
docker-compose up -d

# 4. Проверьте что модель загружена
curl http://localhost:11434/api/tags
```

### Q: Watcher слишком часто запускает исправления?
**A:** Увеличьте параметры в `watcher.py`:
```python
POLL_INTERVAL = 120       # Опрос каждые 2 минуты вместо 30 сек
ERROR_THRESHOLD = 10      # Порог с 3 до 10 ошибок
```
Затем пересоздайте контейнер: `docker-compose up -d --force-recreate watcher`

### Q: Можно ли использовать с облачным Ollama?
**A:** Да, измените `OLLAMA_HOST` на адрес вашего облачного сервера:
```yaml
environment:
  - OLLAMA_HOST=https://your-ollama-server.com:11434
```
Убедитесь что сервер доступен из Docker сети.

### Q: Как добавить аутентификацию в API?
**A:** Добавьте middleware в `app.py`:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("API_TOKEN", "secret-token")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

@app.get("/protected")
async def protected(token: str = Depends(verify_token)):
    return {"message": "Access granted", "token": token[:8] + "..."}
```
Не забудьте установить `API_TOKEN` в环境变量.

### Q: Ошибка "Docker permission denied"?
**A:** Убедитесь что пользователь имеет доступ к docker.sock:
```bash
# Проверьте права
ls -la /var/run/docker.sock

# Добавьте пользователя в группу docker (на хосте)
sudo usermod -aG docker $USER

# Или используйте root в контейнере (уже настроено)
```

### Q: Как экспортировать конфигурацию агентов?
**A:** Сохраните результаты работы через API:
```bash
curl http://localhost:8000/results > agent_results.json
```
Или скопируйте логи:
```bash
docker cp devops_crew:/app/logs ./exported_logs
```

### Q: Можно ли запускать несколько экземпляров системы?
**A:** Да, но с разными именами проектов:
```bash
# Проект 1
COMPOSE_PROJECT_NAME=devops1 docker-compose up -d

# Проект 2 (измените порты в копии docker-compose.yml)
COMPOSE_PROJECT_NAME=devops2 docker-compose -f docker-compose-2.yml up -d
```

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push на branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🙏 Благодарности

- [CrewAI](https://github.com/joaomdmoura/crewai) - фреймворк для оркестрации агентов
- [Ollama](https://github.com/ollama/ollama) - локальные LLM
- [Streamlit](https://streamlit.io/) - веб-интерфейс
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Docker](https://www.docker.com/) - контейнеризация

---

**Создано с ❤️ для автоматизации DevOps задач**

*Версия: 1.0 | Последнее обновление: 2024*
