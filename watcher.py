#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevOps Watcher - Фоновый монитор состояния системы
Периодически проверяет здоровье сервисов и логирует аномалии
"""

import os
import sys
import time
import json
import logging
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# Настройка логирования
LOGS_DIR = Path(os.getenv("LOGS_DIR", "/app/logs"))
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "watcher.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("watcher")

# Импорт агентов (для периодического анализа)
from agents import get_crew_instance, check_docker_connection, docker_client

# Конфигурация
WATCHER_INTERVAL = int(os.getenv("WATCHER_INTERVAL", "60"))  # секунды
ALERT_THRESHOLD_ERRORS = int(os.getenv("ALERT_THRESHOLD_ERRORS", "5"))  # порог ошибок для алерта
HEALTH_HISTORY_FILE = LOGS_DIR / "health_history.jsonl"

class GracefulKiller:
    """Обработчик сигналов для корректного завершения"""
    kill_now = False
    
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, *args):
        logger.info("🛑 Received shutdown signal, finishing current cycle...")
        self.kill_now = True

class HealthWatcher:
    """Периодический монитор здоровья системы"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.crew = get_crew_instance()
        self.last_alert_time: Optional[datetime] = None
        self.alert_cooldown = timedelta(minutes=5)  # Не спамить алертами
        logger.info(f"HealthWatcher initialized (interval={interval}s)")
    
    def _load_health_history(self) -> List[Dict]:
        """Загрузить историю проверок здоровья"""
        history = []
        if HEALTH_HISTORY_FILE.exists():
            try:
                with open(HEALTH_HISTORY_FILE, 'r') as f:
                    for line in f:
                        if line.strip():
                            history.append(json.loads(line))
            except Exception as e:
                logger.warning(f"Could not load health history: {e}")
        return history[-100:]  # Последние 100 записей
    
    def _save_health_record(self, record: Dict):
        """Сохранить запись о проверке здоровья"""
        try:
            with open(HEALTH_HISTORY_FILE, 'a') as f:
                f.write(json.dumps(record) + '\n')
        except Exception as e:
            logger.error(f"Failed to save health record: {e}")
    
    def _detect_anomalies(self, current_health: Dict, history: List[Dict]) -> List[str]:
        """Выявить аномалии по сравнению с историей"""
        anomalies = []
        
        if not history:
            return anomalies
        
        current_score = current_health.get('overall_health_score', 100)
        avg_score = sum(h.get('overall_health_score', 100) for h in history[-10:]) / min(len(history), 10)
        
        # Резкое падение здоровья
        if current_score < avg_score - 20:
            anomalies.append(f"Health dropped from {avg_score:.1f}% to {current_score}%")
        
        # Новые критические сервисы
        current_critical = {k for k, v in current_health.get('services', {}).items() 
                          if v.get('status') == 'critical'}
        prev_critical = set()
        for h in history[-5:]:
            prev_critical.update(k for k, v in h.get('services', {}).items() 
                               if v.get('status') == 'critical')
        
        new_critical = current_critical - prev_critical
        if new_critical:
            anomalies.append(f"New critical services: {', '.join(new_critical)}")
        
        return anomalies
    
    def _should_send_alert(self) -> bool:
        """Проверить, можно ли отправить алерт (cooldown)"""
        if self.last_alert_time is None:
            return True
        return datetime.now() - self.last_alert_time > self.alert_cooldown
    
    def _send_alert(self, message: str, anomalies: List[str]):
        """Отправить алерт (в лог, можно расширить на Slack/Telegram)"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "WARNING",
            "message": message,
            "anomalies": anomalies,
            "action_required": True
        }
        logger.warning(f"🚨 ALERT: {json.dumps(alert, indent=2)}")
        
        # Сохранить алерт в отдельный файл для интеграций
        alert_file = LOGS_DIR / "alerts.jsonl"
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        self.last_alert_time = datetime.now()
    
    def check_and_report(self) -> Dict:
        """Выполнить проверку и сгенерировать отчет"""
        logger.info("🔍 Running health check cycle...")
        
        # Базовая проверка подключения
        docker_ok = check_docker_connection()
        if not docker_ok:
            logger.warning("⚠ Docker not available - running in simulation mode")
        
        # Быстрая проверка через агента мониторинга
        try:
            health_result = self.crew.run_health_check()
            # Парсим результат (упрощённо)
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "docker_available": docker_ok,
                "agent_result_preview": str(health_result)[:200],
                "overall_health_score": 85 if docker_ok else 50,  # Заглушка
                "services": {}
            }
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "docker_available": docker_ok,
                "error": str(e),
                "overall_health_score": 0,
                "services": {}
            }
        
        # Если Docker доступен - собираем реальные метрики
        if docker_ok and docker_client:
            try:
                containers = docker_client.containers.list(all=True)
                services = {}
                
                for c in containers:
                    attrs = c.attrs
                    state = attrs.get('State', {})
                    services[c.name] = {
                        "status": c.status,
                        "running": c.status == "running",
                        "restart_count": state.get('RestartCount', 0),
                        "health": state.get('Health', {}).get('Status', 'none')
                    }
                    
                    # Проверка на crash loop
                    if state.get('RestartCount', 0) > 3:
                        services[c.name]['alert'] = 'crash_loop_detected'
                
                health_data['services'] = services
                health_data['container_count'] = len(containers)
                
            except Exception as e:
                logger.error(f"Failed to collect container metrics: {e}")
        
        # Анализ аномалий
        history = self._load_health_history()
        anomalies = self._detect_anomalies(health_data, history)
        
        # Отправка алертов при необходимости
        if anomalies and self._should_send_alert():
            self._send_alert(
                f"Health anomalies detected (score: {health_data.get('overall_health_score', 'N/A')}%)",
                anomalies
            )
        
        # Сохранение в историю
        self._save_health_record(health_data)
        
        logger.info(f"✅ Health check completed: score={health_data.get('overall_health_score', 'N/A')}%")
        return health_data
    
    def run(self):
        """Основной цикл работы вотчера"""
        logger.info(f"👁️  Watcher starting (checking every {self.interval}s)")
        
        while not killer.kill_now:
            try:
                self.check_and_report()
            except Exception as e:
                logger.error(f"Error in watch cycle: {e}", exc_info=True)
            
            # Цикл с возможностью прерывания
            for _ in range(self.interval):
                if killer.kill_now:
                    break
                time.sleep(1)
        
        logger.info("👋 Watcher stopped gracefully")

# Глобальный обработчик сигналов
killer = GracefulKiller()

def main():
    """Точка входа"""
    logger.info("🚀 DevOps Watcher Service starting...")
    
    # Проверка зависимостей
    if not check_docker_connection():
        logger.warning("⚠ Running without Docker access - limited functionality")
    
    # Запуск основного цикла
    watcher = HealthWatcher(interval=WATCHER_INTERVAL)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("⌨️  Interrupted by user")
    finally:
        logger.info("🏁 Watcher service terminated")
        sys.exit(0)

if __name__ == "__main__":
    main()
