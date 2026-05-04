# 🤖 DevOps Multi-Agent System

Локальная мульти-агентная система для автоматизации DevOps задач на базе **CrewAI + Ollama + docker-py** с веб-интерфейсом.

## 🎯 Возможности

Система автоматически:
- ✅ **Разворачивает Docker Compose проекты** - анализ конфигурации и деплой
- 📊 **Анализирует логи контейнеров** - поиск ошибок, аномалий и паттернов
- 🔧 **Исправляет ошибки** - автоматическое применение исправлений
- 📈 **Мониторит работоспособность** - проверка здоровья сервисов 24/7

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
│  │  │   Agent     │ │  (Background)                     │   │
│  │  └─────────────┘ └─────────────┘                     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Docker Socket + Ollama API
┌──────────────────────▼──────────────────────────────────────┐
│  Ollama (LLM)        │        Docker Daemon                 │
│  Port: 11434         │        /var/run/docker.sock          │
│  Model: mistral      │        Containers                    │
└──────────────────────┴──────────────────────────────────────┘
```

## 📁 Структура проекта

```
/workspace
├── docker-compose.yml      # Основная конфигурация Docker Compose
├── Dockerfile.backend      # Dockerfile для backend с агентами
├── Dockerfile.ui           # Dockerfile для веб-интерфейса
├── requirements.txt        # Python зависимости
├── agents.py               # Определение ИИ-агентов и задач CrewAI
├── app.py                  # FastAPI backend приложение
├── web_ui.py               # Streamlit веб-интерфейс
├── watcher.py              # Фоновый наблюдатель для авто-мониторинга
└── README.md               # Этот файл
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

# 2. Загрузите модель Ollama (mistral)
docker run --rm ollama/ollama ollama pull mistral

# 3. Запустите всю систему
docker-compose up -d

# 4. Проверьте статус
docker-compose ps

# 5. Откройте веб-интерфейс
# http://localhost:8501
```

### Остановка системы

```bash
docker-compose down
# или с удалением данных
docker-compose down -v
```

## 🎭 ИИ-Агенты

Система использует 4 специализированных агента на базе CrewAI:

### 1. 🚀 Deployment Agent
**Роль:** DevOps Deployment Engineer  
**Задачи:**
- Анализ конфигураций Docker Compose
- Развертывание сервисов в правильном порядке
- Проверка конфликтов портов
- Управление жизненным циклом контейнеров

### 2. 📊 Log Analyzer Agent
**Роль:** Senior Log Analyst  
**Задачи:**
- Анализ логов на наличие ошибок (ERROR, FATAL, CRITICAL)
- Выявление паттернов и аномалий
- Определение корневых причин проблем
- Приоритизация проблем по критичности

### 3. 🔧 Fix Agent
**Роль:** DevOps Troubleshooter  
**Задачи:**
- Автоматическое исправление конфигураций
- Перезапуск проблемных сервисов
- Генерация исправленных docker-compose.yml
- Валидация примененных исправлений

### 4. 📈 Monitoring Agent
**Роль:** System Health Monitor  
**Задачи:**
- Постоянный мониторинг статуса контейнеров
- Проверка использования ресурсов
- Обнаружение restart loop
- Формирование дашборда здоровья (0-100%)

## 🌐 Веб-интерфейс

Веб-интерфейс доступен по адресу **http://localhost:8501** и включает 5 вкладок:

### 📊 Дашборд
- Статус всех контейнеров в реальном времени
- Метрики: всего/запущено/остановлено
- Таблица контейнеров с деталями
- Результаты последнего мониторинга

### 🚀 Развертывание
- Редактор Docker Compose конфигураций
- Валидация YAML синтаксиса
- Деплой через ИИ-агента
- Отчет о процессе развертывания

### 📝 Логи
- Выбор контейнеров для анализа
- Просмотр логов в реальном времени
- ИИ-анализ ошибок с рекомендациями
- Экспорт отчетов

### 🔧 Исправление
- Автоматическое исправление найденных ошибок
- Использование контекста из анализа логов
- Отчет о примененных изменениях

### ⚙️ Управление
- Старт/стоп/рестарт контейнеров
- Детальная информация о контейнере
- Быстрые действия через боковую панель

## 📡 API Endpoints

Backend API доступен по адресу **http://localhost:8000**

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Статус API |
| GET | `/health` | Проверка здоровья |
| GET | `/containers` | Список контейнеров |
| GET | `/containers/{name}/logs` | Логи контейнера |
| POST | `/containers/action` | Действие (start/stop/restart) |
| POST | `/deploy` | Развернуть Compose проект |
| POST | `/analyze-logs` | Анализ логов через ИИ |
| POST | `/fix` | Исправление ошибок через ИИ |
| GET | `/monitor` | Запуск мониторинга |
| POST | `/full-cycle` | Полный цикл (деплой→мониторинг→анализ→фикс) |
| GET | `/results` | Последние результаты |

### Примеры использования API

```bash
# Получить список контейнеров
curl http://localhost:8000/containers

# Развернуть Docker Compose проект
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "compose_config": "version: \"3.8\"\nservices:\n  web:\n    image: nginx:latest\n    ports:\n      - \"80:80\"",
    "project_name": "my_project"
  }'

# Проанализировать логи
curl -X POST http://localhost:8000/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{
    "container_names": ["devops_ollama", "devops_crew"],
    "tail_lines": 200
  }'

# Запустить полный цикл
curl -X POST http://localhost:8000/full-cycle
```

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

Сервис `watcher` работает в фоне и автоматически:

1. **Опрашивает контейнеры** каждые 30 секунд
2. **Ищет ошибки** в логах (ERROR, FATAL, CRITICAL, Exception)
3. **Накопляет историю** ошибок по каждому контейнеру
4. **Запускает ИИ-анализ** при достижении порога (3 ошибки)
5. **Применяет исправления** через Fix Agent

### Настройка Watcher

В `watcher.py` можно изменить параметры:

```python
POLL_INTERVAL = 30      # Интервал опроса (секунды)
ERROR_THRESHOLD = 3     # Порог ошибок для запуска ИИ
```

## 📊 Логирование

Логи системы сохраняются в директорию `/workspace/logs`:

```
logs/
├── compose_my_project_20240101_120000.yml  # Сохраненные конфиги
├── agent_logs_20240101.log                 # Логи работы агентов
└── watcher_20240101.log                    # Логи наблюдателя
```

Просмотр логов:

```bash
# Логи backend
docker logs devops_crew -f

# Логи веб-интерфейса
docker logs devops_ui -f

# Логи наблюдателя
docker logs devops_watcher -f

# Логи Ollama
docker logs devops_ollama -f
```

## 🛡️ Безопасность

### Важные замечания

⚠️ **Docker Socket Access**: Система имеет доступ к `/var/run/docker.sock`, что дает полный контроль над Docker хоста. Используйте только в доверенной среде!

⚠️ **Авто-исправления**: Watcher может автоматически перезапускать контейнеры и применять исправления. Для production рекомендуется отключить авто-фикс:

```yaml
# В docker-compose.yml закомментировать сервис watcher
# watcher:
#   ...
```

### Рекомендации для production

1. Изолируйте систему в отдельной сети
2. Используйте read-only доступ к Docker socket где возможно
3. Настройте аутентификацию для API
4. Ограничьте права агентов через RBAC

## 🧪 Тестирование

### Проверка работы системы

```bash
# 1. Проверьте что все сервисы запущены
docker-compose ps

# 2. Проверьте подключение к Ollama
curl http://localhost:11434/api/tags

# 3. Проверьте API backend
curl http://localhost:8000/health

# 4. Создайте тестовый контейнер
docker run -d --name test_container nginx:latest

# 5. Запустите мониторинг через API
curl http://localhost:8000/monitor

# 6. Проверьте что агент видит тестовый контейнер
curl http://localhost:8000/containers
```

### Сценарий тестирования полного цикла

```bash
# 1. Создайте проблемный контейнер
docker run -d --name broken_app alpine sh -c "while true; do echo 'ERROR: Connection failed'; sleep 5; done"

# 2. Запустите анализ логов
curl -X POST http://localhost:8000/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{"container_names": ["broken_app"]}'

# 3. Запустите полный цикл исправления
curl -X POST http://localhost:8000/full-cycle

# 4. Очистите тестовый контейнер
docker rm -f broken_app
```

## 🔧 Расширение функциональности

### Добавление новых агентов

В файле `agents.py` добавьте нового агента:

```python
new_agent = Agent(
    role='New Specialist',
    goal='Describe the goal',
    backstory='Detailed backstory...',
    verbose=True,
    llm=llm
)
```

### Добавление новых инструментов

```python
def custom_tool():
    """Description of the tool"""
    # Your implementation
    return result

DOCKER_TOOLS.append(custom_tool)
```

### Интеграция с другими системами

Система легко расширяется для интеграции с:
- Kubernetes (через kubernetes-python)
- Prometheus/Grafana (метрики)
- Slack/Telegram (уведомления)
- CI/CD системы (GitLab CI, GitHub Actions)

## 📈 Производительность

### Требования к ресурсам

| Компонент | RAM | CPU | Disk |
|-----------|-----|-----|------|
| Ollama (mistral) | 4-8 GB | 2 cores | 5 GB |
| Backend + Agents | 2-4 GB | 1-2 cores | 2 GB |
| Web UI | 500 MB | 0.5 cores | 500 MB |
| **Итого** | **~8-16 GB** | **4-5 cores** | **~10 GB** |

### Оптимизация производительности

1. **Используйте меньшие модели** для быстрых задач:
   ```bash
   ollama pull mistral:7b
   ```

2. **Настройте кэширование** ответов агентов

3. **Увеличьте интервал** опроса Watcher в production

4. **Используйте GPU** если доступно (добавьте в docker-compose.yml):
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

## ❓ FAQ

### Q: Агенты работают медленно?
**A:** Это нормально для локальных LLM. Для ускорения:
- Используйте меньшую модель (mistral:7b вместо mistral)
- Уменьшите `temperature` в настройках LLM
- Добавьте GPU поддержку

### Q: Как сменить модель LLM?
**A:** Измените `MODEL_NAME` в `docker-compose.yml` и пересоздайте контейнеры:
```bash
docker-compose down
# Измените MODEL_NAME в docker-compose.yml
docker-compose up -d
```

### Q: Watcher слишком часто запускает исправления?
**A:** Увеличьте `ERROR_THRESHOLD` в `watcher.py` или увеличьте `POLL_INTERVAL`.

### Q: Можно ли использовать с облачным Ollama?
**A:** Да, измените `OLLAMA_HOST` на адрес вашего облачного сервера.

### Q: Как добавить аутентификацию в API?
**A:** Добавьте middleware в `app.py`:
```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.get("/protected")
async def protected(token: str = Depends(security)):
    # Validate token
    pass
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
