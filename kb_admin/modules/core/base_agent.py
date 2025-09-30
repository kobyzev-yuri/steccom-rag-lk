"""
Base Agent Class для KB Admin
Базовый класс для всех агентов системы KB Admin
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """Базовый класс для всех агентов системы KB Admin"""
    
    def __init__(self, agent_name: str, model_type: str = "chat"):
        self.agent_name = agent_name
        self.model_type = model_type
        self.model_name = "qwen3:8b"  # Дефолтная модель для KB Admin
        self.ollama_base_url = "http://localhost:11434"
        self.db_path = "satellite_billing.db"  # Путь к БД KB Admin
        
        # Инициализируем chat модель
        self._init_chat_model()
        
        # Инициализируем таблицу учета токенов
        self._ensure_usage_table()
        
        logger.info(f"Инициализирован агент {agent_name} с моделью {self.model_name}")
    
    def _init_chat_model(self):
        """Инициализация chat модели"""
        try:
            from langchain_community.chat_models import ChatOllama
            from langchain_openai import ChatOpenAI
            import os
            
            # Проверяем, какой провайдер использовать
            use_proxy = os.getenv("USE_PROXYAPI", "false").lower() == "true"
            
            if use_proxy:
                # Используем ProxyAPI
                api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
                base_url = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
                model = os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o")
                
                if api_key:
                    self.chat_model = ChatOpenAI(
                        model=model,
                        openai_api_key=api_key,
                        base_url=base_url,
                        temperature=0.2
                    )
                    self._chat_backend = {
                        'provider': 'proxyapi', 
                        'model': model,
                        'base_url': base_url
                    }
                else:
                    # Fallback to Ollama
                    self.chat_model = ChatOllama(model=self.model_name, timeout=10)
                    self._chat_backend = {'provider': 'ollama', 'model': self.model_name}
            else:
                # Используем Ollama по умолчанию
                self.chat_model = ChatOllama(model=self.model_name, timeout=10)
                self._chat_backend = {'provider': 'ollama', 'model': self.model_name}
                
        except Exception as e:
            logger.error(f"Ошибка инициализации chat модели: {e}")
            # Fallback к простой модели
            try:
                from langchain_community.chat_models import ChatOllama
                self.chat_model = ChatOllama(model=self.model_name, timeout=10)
                self._chat_backend = {'provider': 'ollama', 'model': self.model_name}
            except Exception:
                self.chat_model = None
                self._chat_backend = {'provider': 'none', 'model': 'none'}
    
    def set_chat_backend(self, provider: str, model: str, base_url: str = None, 
                        api_key: str = None, temperature: float = 0.2):
        """Переключить chat backend"""
        try:
            if provider == "ollama":
                from langchain_community.chat_models import ChatOllama
                self.chat_model = ChatOllama(model=model, timeout=10)
                self._chat_backend = {'provider': 'ollama', 'model': model}
                self.model_name = model
                
            elif provider == "proxyapi":
                from langchain_openai import ChatOpenAI
                resolved_base_url = base_url or os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
                resolved_api_key = api_key or os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
                
                if resolved_api_key:
                    self.chat_model = ChatOpenAI(
                        model=model,
                        openai_api_key=resolved_api_key,
                        base_url=resolved_base_url,
                        temperature=temperature
                    )
                    self._chat_backend = {
                        'provider': 'proxyapi', 
                        'model': model,
                        'base_url': resolved_base_url,
                        'temperature': temperature
                    }
                    self.model_name = model
                else:
                    raise ValueError("API ключ не предоставлен для ProxyAPI")
                    
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                openai_key = api_key or os.getenv("OPENAI_API_KEY")
                
                if openai_key:
                    self.chat_model = ChatOpenAI(
                        model=model,
                        openai_api_key=openai_key,
                        temperature=temperature
                    )
                    self._chat_backend = {
                        'provider': 'openai', 
                        'model': model,
                        'temperature': temperature
                    }
                    self.model_name = model
                else:
                    raise ValueError("API ключ не предоставлен для OpenAI")
            
            logger.info(f"Агент {self.agent_name} переключен на {provider}:{model}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переключения backend: {e}")
            return False
    
    def get_chat_backend_info(self):
        """Получить информацию о текущем chat backend"""
        return self._chat_backend.copy() if hasattr(self, '_chat_backend') else {}
    
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
        self.model_name = new_model
        logger.info(f"Агент {self.agent_name} переключен на модель {new_model}")
        return True
    
    def get_available_models(self) -> Dict[str, str]:
        """Получить список доступных моделей"""
        return {
            "chat": "qwen3:8b",
            "sql": "qwen3:8b", 
            "embedding": "all-minilm",
            "vision": "llava-phi3:latest",
            "document_analysis": "qwen3:8b",
            "text_extraction": "qwen3:8b",
            "content_categorization": "qwen3:8b"
        }
    
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
