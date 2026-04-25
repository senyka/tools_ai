import streamlit as st
import requests
import json
import time
from datetime import datetime

import os

# Конфигурация
BACKEND_URL = os.getenv("BACKEND_URL", "http://crewai_backend:8800")

st.set_page_config(
    page_title="DevOps Multi-Agent System",
    page_icon="🤖",
    layout="wide"
)

# ==================== СТИЛИ ====================

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center;}
    .sub-header {font-size: 1.2rem; color: #666;}
    .status-box {padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
    .success {background-color: #d4edda; border-left: 4px solid #28a745;}
    .warning {background-color: #fff3cd; border-left: 4px solid #ffc107;}
    .error {background-color: #f8d7da; border-left: 4px solid #dc3545;}
    .info {background-color: #d1ecf1; border-left: 4px solid #17a2b8;}
    .code-block {background-color: #f4f4f4; padding: 1rem; border-radius: 0.5rem; overflow-x: auto;}
</style>
""", unsafe_allow_html=True)

# ==================== ЗАГОЛОВОК ====================

st.markdown("<h1 class='main-header'>🤖 DevOps Multi-Agent System</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header' style='text-align: center;'>Автоматизированная система управления Docker с ИИ-агентами на базе CrewAI + Ollama</p>", unsafe_allow_html=True)

st.divider()

# ==================== БОКОВАЯ ПАНЕЛЬ ====================

with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Проверка подключения к бэкенду
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health_data = health_response.json()
        st.success("✅ Бэкенд подключен")
        st.info(f"🐳 Docker: {health_data.get('docker_status', 'unknown')}")
    except Exception as e:
        st.error(f"❌ Бэкенд недоступен: {str(e)}")
    
    st.divider()
    
    # Быстрые действия
    st.subheader("⚡ Быстрые действия")
    
    if st.button("🔄 Обновить данные", use_container_width=True):
        st.rerun()
    
    if st.button("📊 Запустить мониторинг", use_container_width=True):
        try:
            with st.spinner("Агенты анализируют систему..."):
                response = requests.get(f"{BACKEND_URL}/monitor", timeout=60)
                st.session_state['monitor_result'] = response.json()
            st.success("Мониторинг завершен!")
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
    
    if st.button("🔍 Полный цикл анализа", use_container_width=True):
        try:
            with st.spinner("Запуск полного цикла (деплой → мониторинг → анализ → исправление)..."):
                response = requests.post(f"{BACKEND_URL}/full-cycle", timeout=120)
                st.session_state['full_cycle_result'] = response.json()
            st.success("Полный цикл завершен!")
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
    
    st.divider()
    
    # Последние результаты
    st.subheader("📋 Последние результаты")
    if 'last_update' in st.session_state:
        st.caption(f"Обновлено: {st.session_state['last_update']}")
    else:
        st.caption("Нет данных")

# ==================== ОСНОВНАЯ ЧАСТЬ ====================

# Вкладка 1: Дашборд
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Дашборд",
    "🚀 Развертывание",
    "📝 Логи",
    "🔧 Исправление",
    "⚙️ Управление"
])

# ===== ВКЛАДКА 1: ДАШБОРД =====
with tab1:
    st.header("📊 Дашборд состояния системы")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Получение списка контейнеров
    try:
        containers_response = requests.get(f"{BACKEND_URL}/containers", timeout=10)
        containers_data = containers_response.json()
        containers = containers_data.get('containers', [])
        
        running_count = sum(1 for c in containers if c.get('status') == 'running')
        stopped_count = sum(1 for c in containers if c.get('status') == 'exited')
        
        col1.metric("Всего контейнеров", len(containers))
        col2.metric("Запущено", running_count, delta_color="normal")
        col3.metric("Остановлено", stopped_count, delta_color="inverse")
        col4.metric("Время работы", datetime.now().strftime("%H:%M:%S"))
        
    except Exception as e:
        col1.error(f"Ошибка получения данных: {str(e)}")
        containers = []
    
    st.divider()
    
    # Таблица контейнеров
    st.subheader("📦 Контейнеры")
    if containers:
        container_data = []
        for c in containers:
            status_emoji = "🟢" if c.get('status') == 'running' else "🔴"
            container_data.append({
                "Статус": status_emoji,
                "Имя": c.get('name', 'N/A'),
                "Статус": c.get('status', 'unknown'),
                "Образ": c.get('image', 'N/A'),
                "Создан": c.get('created', 'N/A')[:19] if c.get('created') else 'N/A'
            })
        
        st.dataframe(container_data, use_container_width=True, hide_index=True)
    else:
        st.info("Контейнеры не найдены или невозможно получить данные")
    
    st.divider()
    
    # Результаты мониторинга
    st.subheader("📈 Результаты последнего мониторинга")
    if 'monitor_result' in st.session_state:
        result = st.session_state['monitor_result']
        st.json(result.get('health_report', 'Нет данных'))
    else:
        st.info("Запустите мониторинг через боковую панель")

# ===== ВКЛАДКА 2: РАЗВЕРТЫВАНИЕ =====
with tab2:
    st.header("🚀 Развертывание Docker Compose")
    
    st.markdown("""
    ### Инструкция:
    1. Вставьте конфигурацию docker-compose.yml
    2. Укажите имя проекта
    3. Нажмите "Развернуть"
    4. ИИ-агент проанализирует конфигурацию и выполнит развертывание
    """)
    
    compose_config = st.text_area(
        "Конфигурация Docker Compose (YAML)",
        height=300,
        placeholder="""version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: example"""
    )
    
    project_name = st.text_input("Имя проекта", value="my_project")
    
    col1, col2 = st.columns(2)
    with col1:
        deploy_btn = st.button("🚀 Развернуть проект", use_container_width=True, type="primary")
    with col2:
        validate_btn = st.button("✓ Проверить конфиг", use_container_width=True)
    
    if deploy_btn and compose_config:
        with st.spinner("🤖 ИИ-агент анализирует и разворачивает проект..."):
            try:
                payload = {
                    "compose_config": compose_config,
                    "project_name": project_name
                }
                response = requests.post(f"{BACKEND_URL}/deploy", json=payload, timeout=300)
                result = response.json()
                
                if result.get('status') == 'success':
                    st.success("✅ Развертывание успешно!")
                    st.expander("📄 Отчет агента").write(result.get('data', {}).get('result', 'Нет данных'))
                    st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    st.error(f"❌ Ошибка: {result.get('detail', 'Неизвестная ошибка')}")
            except Exception as e:
                st.error(f"Ошибка подключения: {str(e)}")
    
    if validate_btn and compose_config:
        st.info("ℹ️ Функция валидации будет добавлена в следующей версии")

# ===== ВКЛАДКА 3: ЛОГИ =====
with tab3:
    st.header("📝 Анализ логов")
    
    # Выбор контейнера
    container_names = []
    try:
        containers_response = requests.get(f"{BACKEND_URL}/containers", timeout=10)
        containers = containers_response.json().get('containers', [])
        container_names = [c.get('name') for c in containers if c.get('name')]
        
        if container_names:
            selected_containers = st.multiselect(
                "Выберите контейнеры для анализа",
                container_names,
                default=container_names[:3] if len(container_names) > 3 else container_names
            )
            
            tail_lines = st.slider("Количество строк логов", 50, 500, 100)
            
            if st.button("🔍 Анализировать логи", type="primary"):
                if selected_containers:
                    with st.spinner("🤖 ИИ-агент анализирует логи..."):
                        try:
                            payload = {
                                "container_names": selected_containers,
                                "tail_lines": tail_lines
                            }
                            response = requests.post(f"{BACKEND_URL}/analyze-logs", json=payload, timeout=120)
                            result = response.json()
                            
                            if result.get('status') == 'success':
                                st.success("✅ Анализ завершен!")
                                st.expander("📄 Отчет ИИ-агента").write(result.get('analysis', 'Нет данных'))
                                st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                st.error(f"Ошибка: {result.get('detail', 'Неизвестная ошибка')}")
                        except Exception as e:
                            st.error(f"Ошибка подключения: {str(e)}")
                else:
                    st.warning("Выберите хотя бы один контейнер")
        else:
            st.info("Нет доступных контейнеров для анализа")
            
    except Exception as e:
        st.error(f"Ошибка получения списка контейнеров: {str(e)}")
    
    st.divider()
    
    # Просмотр логов конкретного контейнера
    st.subheader("📋 Просмотр логов контейнера")
    if container_names:
        selected_container = st.selectbox("Выберите контейнер", container_names)
        log_lines = st.number_input("Строк логов", min_value=10, max_value=1000, value=100)
        
        if st.button("📖 Показать логи"):
            try:
                response = requests.get(f"{BACKEND_URL}/containers/{selected_container}/logs?tail={log_lines}", timeout=10)
                result = response.json()
                st.code(result.get('logs', 'Нет данных'), language="text")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

# ===== ВКЛАДКА 4: ИСПРАВЛЕНИЕ =====
with tab4:
    st.header("🔧 Автоматическое исправление ошибок")
    
    st.markdown("""
    ### Как это работает:
    1. Вставьте отчет об ошибках (или используйте последний анализ логов)
    2. ИИ-агент проанализирует проблемы
    3. Агент предложит и применит исправления
    4. Вы получите отчет о внесенных изменениях
    """)
    
    error_report = st.text_area(
        "Отчет об ошибках",
        height=200,
        placeholder="Вставьте текст ошибки или отчета из анализа логов..."
    )
    
    # Кнопка использования последнего анализа
    if 'monitor_result' in st.session_state or 'full_cycle_result' in st.session_state:
        if st.button("📋 Использовать последний анализ"):
            last_result = st.session_state.get('full_cycle_result', st.session_state.get('monitor_result', {}))
            error_report = str(last_result.get('results', {}).get('log_analysis', 'Нет данных'))
    
    if st.button("🔧 Исправить ошибки", type="primary"):
        if error_report:
            with st.spinner("🤖 ИИ-агент анализирует ошибки и применяет исправления..."):
                try:
                    payload = {"error_report": error_report}
                    response = requests.post(f"{BACKEND_URL}/fix", json=payload, timeout=120)
                    result = response.json()
                    
                    if result.get('status') == 'success':
                        st.success("✅ Исправления применены!")
                        st.expander("📄 Отчет об исправлениях").write(result.get('fixes_applied', 'Нет данных'))
                        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        st.error(f"Ошибка: {result.get('detail', 'Неизвестная ошибка')}")
                except Exception as e:
                    st.error(f"Ошибка подключения: {str(e)}")
        else:
            st.warning("Введите отчет об ошибках")

# ===== ВКЛАДКА 5: УПРАВЛЕНИЕ =====
with tab5:
    st.header("⚙️ Управление контейнерами")
    
    try:
        containers_response = requests.get(f"{BACKEND_URL}/containers", timeout=10)
        containers = containers_response.json().get('containers', [])
        
        if containers:
            selected_container = st.selectbox(
                "Выберите контейнер",
                [c.get('name') for c in containers]
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("▶️ Старт", use_container_width=True):
                    try:
                        payload = {"container_name": selected_container, "action": "start"}
                        response = requests.post(f"{BACKEND_URL}/containers/action", json=payload, timeout=30)
                        st.success(response.json().get('message', 'Выполнено'))
                    except Exception as e:
                        st.error(str(e))
            
            with col2:
                if st.button("⏹️ Стоп", use_container_width=True):
                    try:
                        payload = {"container_name": selected_container, "action": "stop"}
                        response = requests.post(f"{BACKEND_URL}/containers/action", json=payload, timeout=30)
                        st.success(response.json().get('message', 'Выполнено'))
                    except Exception as e:
                        st.error(str(e))
            
            with col3:
                if st.button("🔄 Рестарт", use_container_width=True):
                    try:
                        payload = {"container_name": selected_container, "action": "restart"}
                        response = requests.post(f"{BACKEND_URL}/containers/action", json=payload, timeout=30)
                        st.success(response.json().get('message', 'Выполнено'))
                    except Exception as e:
                        st.error(str(e))
            
            with col4:
                if st.button("🗑️ Удалить", use_container_width=True):
                    st.warning("Функция удаления будет добавлена в следующей версии")
            
            st.divider()
            
            # Информация о выбранном контейнере
            container_info = next((c for c in containers if c.get('name') == selected_container), None)
            if container_info:
                st.subheader(f"📦 Информация: {selected_container}")
                st.json(container_info)
        else:
            st.info("Нет доступных контейнеров")
            
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")

# ==================== ПОДВАЛ ====================

st.divider()
st.caption("""
DevOps Multi-Agent System v1.0 | Powered by CrewAI + Ollama + Docker
""")
