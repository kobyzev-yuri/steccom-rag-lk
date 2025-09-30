"""
Base Agent Class
Базовый класс для всех агентов системы
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Добавляем путь к конфигурации
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import MODELS, OLLAMA_BASE_URL, DATABASE_PATH

logger = logging.getLogger(__name__)

class BaseAgent:
    """Базовый класс для всех агентов системы"""
    
    def __init__(self, agent_name: str, model_type: str = "chat"):
        self.agent_name = agent_name
        self.model_type = model_type
        self.model_name = MODELS.get(model_type, MODELS["chat"])
        self.ollama_base_url = OLLAMA_BASE_URL
        self.db_path = DATABASE_PATH
        
        # Инициализируем таблицу учета токенов
        self._ensure_usage_table()
        
        logger.info(f"Инициализирован агент {agent_name} с моделью {self.model_name}")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Получить конфигурацию модели для агента"""
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "ollama_base_url": self.ollama_base_url,
            "agent_name": self.agent_name
        }
    
    def update_model(self, new_model: str) -> bool:
        """Обновить модель агента"""
        if new_model in MODELS.values():
            self.model_name = new_model
            logger.info(f"Агент {self.agent_name} переключен на модель {new_model}")
            return True
        else:
            logger.warning(f"Модель {new_model} не найдена в конфигурации")
            return False
    
    def get_available_models(self) -> Dict[str, str]:
        """Получить список доступных моделей"""
        return MODELS.copy()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Получить информацию об агенте"""
        return {
            "agent_name": self.agent_name,
            "model_type": self.model_type,
            "model_name": self.model_name,
            "ollama_base_url": self.ollama_base_url,
            "available_models": self.get_available_models()
        }
    
    def _ensure_usage_table(self) -> None:
        """Создать таблицу llm_usage если не существует"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    agent_name TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    question TEXT,
                    response_length INTEGER
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка создания таблицы llm_usage: {e}")
    
    def log_usage(self, provider: Optional[str], model: Optional[str],
                  prompt_tokens: Optional[int], completion_tokens: Optional[int],
                  total_tokens: Optional[int], question: str,
                  response_length: int) -> None:
        """Записать использование токенов в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO llm_usage (
                    timestamp, provider, model, agent_name, prompt_tokens, completion_tokens, total_tokens, question, response_length
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    provider, model, self.agent_name,
                    prompt_tokens if isinstance(prompt_tokens, int) else None,
                    completion_tokens if isinstance(completion_tokens, int) else None,
                    total_tokens if isinstance(total_tokens, int) else None,
                    question, int(response_length)
                )
            )
            conn.commit()
            conn.close()
            logger.info(f"Агент {self.agent_name} использовал {total_tokens or 0} токенов")
        except Exception as e:
            logger.error(f"Ошибка записи использования токенов: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получить статистику использования агента"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Общая статистика агента
            c.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    COALESCE(SUM(prompt_tokens), 0) as total_prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as total_completion_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens
                FROM llm_usage 
                WHERE agent_name = ?
                """,
                (self.agent_name,)
            )
            stats = c.fetchone()
            
            # Статистика по моделям
            c.execute(
                """
                SELECT 
                    model,
                    COUNT(*) as requests,
                    COALESCE(SUM(total_tokens), 0) as tokens
                FROM llm_usage 
                WHERE agent_name = ?
                GROUP BY model
                ORDER BY tokens DESC
                """,
                (self.agent_name,)
            )
            model_stats = c.fetchall()
            
            conn.close()
            
            return {
                "agent_name": self.agent_name,
                "total_requests": stats[0] if stats else 0,
                "total_prompt_tokens": stats[1] if stats else 0,
                "total_completion_tokens": stats[2] if stats else 0,
                "total_tokens": stats[3] if stats else 0,
                "model_breakdown": [
                    {"model": row[0], "requests": row[1], "tokens": row[2]}
                    for row in model_stats
                ]
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}
