"""
Agent Model Manager UI Component
Компонент для управления моделями агентов в KB Admin
"""

import streamlit as st
import subprocess
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AgentModelManager:
    """Менеджер моделей для агентов KB Admin"""
    
    def __init__(self):
        self.available_ollama_models = self._get_ollama_models()
    
    def _get_ollama_models(self) -> List[str]:
        """Получить список доступных моделей Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]  # Get first column (model name)
                        models.append(model_name)
                return models
            else:
                logger.error("Ошибка выполнения ollama list")
                return []
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при получении списка моделей")
            return []
        except FileNotFoundError:
            logger.error("Ollama не найден")
            return []
        except Exception as e:
            logger.error(f"Ошибка получения моделей: {e}")
            return []
    
    def render_agent_model_config(self, agent_name: str, agent_instance, key_prefix: str = ""):
        """Отобразить конфигурацию модели для конкретного агента"""
        st.subheader(f"🤖 {agent_name} - Конфигурация модели")
        
        # Показываем текущую конфигурацию
        current_config = agent_instance.get_chat_backend_info()
        if current_config:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Текущий провайдер:** {current_config.get('provider', 'Неизвестно')}")
            with col2:
                st.info(f"**Текущая модель:** {current_config.get('model', 'Неизвестно')}")
        
        # Выбор провайдера (по умолчанию текущий)
        providers = ["ollama", "proxyapi", "openai"]
        current_provider = (current_config or {}).get('provider', 'ollama')
        try:
            provider_index = providers.index(current_provider)
        except ValueError:
            provider_index = 0
        provider = st.selectbox(
            "Провайдер чата", 
            providers, 
            index=provider_index, 
            key=f"{key_prefix}_provider"
        )
        
        if provider == "ollama":
            self._render_ollama_config(agent_instance, key_prefix)
        elif provider == "proxyapi":
            self._render_proxyapi_config(agent_instance, key_prefix)
        elif provider == "openai":
            self._render_openai_config(agent_instance, key_prefix)
    
    def _render_ollama_config(self, agent_instance, key_prefix: str):
        """Конфигурация Ollama"""
        if self.available_ollama_models:
            # Аккуратно берем текущую модель из info, не требуя полей экземпляра
            info = {}
            try:
                info = agent_instance.get_chat_backend_info() or {}
            except Exception:
                info = {}
            current_model = info.get('model', self.available_ollama_models[0])
            selected_model = st.selectbox(
                "Модель Ollama:",
                self.available_ollama_models,
                index=self.available_ollama_models.index(current_model) if current_model in self.available_ollama_models else 0,
                key=f"{key_prefix}_ollama_model"
            )
            
            if st.button("Применить Ollama", key=f"{key_prefix}_apply_ollama"):
                try:
                    # Некоторые агенты не возвращают bool — считаем успехом при отсутствии исключения
                    agent_instance.set_chat_backend("ollama", selected_model)
                    st.success(f"✅ Применено: Ollama → {selected_model}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
        else:
            st.warning("⚠️ Не удалось получить список моделей Ollama")
            st.info("Убедитесь, что Ollama установлен и запущен")
    
    def _render_proxyapi_config(self, agent_instance, key_prefix: str):
        """Конфигурация ProxyAPI"""
        col1, col2 = st.columns(2)
        
        with col1:
            base_url = st.text_input(
                "Base URL", 
                value=os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"), 
                key=f"{key_prefix}_proxyapi_base"
            )
            model = st.text_input(
                "Модель", 
                value=os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"), 
                key=f"{key_prefix}_proxyapi_model"
            )
        
        with col2:
            api_key = st.text_input(
                "API Key", 
                type="password", 
                value=os.getenv("PROXYAPI_KEY", ""), 
                key=f"{key_prefix}_proxyapi_key"
            )
            temperature = st.slider(
                "Температура", 
                0.0, 1.0, 0.2, 0.1, 
                key=f"{key_prefix}_proxyapi_temp"
            )
        
        if st.button("Применить ProxyAPI", key=f"{key_prefix}_apply_proxyapi"):
            try:
                agent_instance.set_chat_backend(
                    "proxyapi", model, base_url, api_key, temperature
                )
                st.success(f"✅ Применено: ProxyAPI → {model}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
    
    def _render_openai_config(self, agent_instance, key_prefix: str):
        """Конфигурация OpenAI"""
        col1, col2 = st.columns(2)
        
        with col1:
            model = st.text_input(
                "Модель", 
                value=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"), 
                key=f"{key_prefix}_openai_model"
            )
            api_key = st.text_input(
                "API Key", 
                type="password", 
                value=os.getenv("OPENAI_API_KEY", ""), 
                key=f"{key_prefix}_openai_key"
            )
        
        with col2:
            temperature = st.slider(
                "Температура", 
                0.0, 1.0, 0.2, 0.1, 
                key=f"{key_prefix}_openai_temp"
            )
        
        if st.button("Применить OpenAI", key=f"{key_prefix}_apply_openai"):
            try:
                agent_instance.set_chat_backend(
                    "openai", model, api_key=api_key, temperature=temperature
                )
                st.success(f"✅ Применено: OpenAI → {model}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
    
    def render_global_model_settings(self):
        """Отобразить глобальные настройки моделей"""
        st.subheader("🌐 Глобальные настройки моделей")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Переменные окружения:**")
            st.code(f"""
USE_PROXYAPI={os.getenv('USE_PROXYAPI', 'false')}
PROXYAPI_KEY={'*' * 20 if os.getenv('PROXYAPI_KEY') else 'не установлен'}
PROXYAPI_BASE_URL={os.getenv('PROXYAPI_BASE_URL', 'не установлен')}
PROXYAPI_CHAT_MODEL={os.getenv('PROXYAPI_CHAT_MODEL', 'не установлен')}
            """)
        
        with col2:
            st.markdown("**Ollama модели:**")
            if self.available_ollama_models:
                for model in self.available_ollama_models[:5]:  # Показываем первые 5
                    st.text(f"• {model}")
                if len(self.available_ollama_models) > 5:
                    st.text(f"... и еще {len(self.available_ollama_models) - 5}")
            else:
                st.warning("Модели не найдены")
        
        # Кнопка обновления списка моделей
        if st.button("🔄 Обновить список моделей Ollama"):
            self.available_ollama_models = self._get_ollama_models()
            st.rerun()
    
    def render_agent_status(self, agents: Dict[str, any]):
        """Отобразить статус всех агентов"""
        st.subheader("📊 Статус агентов")
        
        for agent_name, agent_instance in agents.items():
            with st.expander(f"🤖 {agent_name}"):
                try:
                    config = agent_instance.get_chat_backend_info()
                    if config:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Провайдер", config.get('provider', 'Неизвестно'))
                        with col2:
                            st.metric("Модель", config.get('model', 'Неизвестно'))
                        with col3:
                            temp = config.get('temperature', 'N/A')
                            st.metric("Температура", temp)
                    else:
                        st.warning("Конфигурация недоступна")
                except Exception as e:
                    st.error(f"Ошибка получения статуса: {e}")
