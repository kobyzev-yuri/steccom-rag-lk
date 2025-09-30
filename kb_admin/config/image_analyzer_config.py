"""
Конфигурация анализатора изображений
Настройки для работы с различными провайдерами анализа изображений
"""

import os
from typing import Dict, Optional

class ImageAnalyzerConfig:
    """Конфигурация для анализатора изображений"""
    
    def __init__(self):
        # Настройки Ollama
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_LLAVA_MODEL", "llava:7b")
        
        # Настройки ProxyAPI
        self.use_proxy_api = os.getenv("USE_PROXY_API", "false").lower() == "true"
        self.proxy_api_key = os.getenv("PROXY_API_KEY")
        self.proxy_api_provider = os.getenv("PROXY_API_PROVIDER", "openai")  # openai, anthropic, gemini
        
        # Модели для разных провайдеров
        self.proxy_models = {
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
            "gemini": os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        }
        
        # Настройки анализа
        self.max_image_size_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "20"))
        self.analysis_timeout = int(os.getenv("ANALYSIS_TIMEOUT", "60"))
        self.temperature = float(os.getenv("ANALYSIS_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("ANALYSIS_MAX_TOKENS", "1000"))
        
        # Настройки извлечения изображений
        self.extract_images_from_pdf = os.getenv("EXTRACT_IMAGES_FROM_PDF", "true").lower() == "true"
        self.max_images_per_document = int(os.getenv("MAX_IMAGES_PER_DOCUMENT", "10"))
        
        # Директории
        self.images_dir = os.getenv("IMAGES_DIR", "data/extracted_images")
        self.temp_dir = os.getenv("TEMP_DIR", "data/temp")
    
    def get_analyzer_config(self) -> Dict:
        """Получить конфигурацию для анализатора"""
        return {
            "ollama_base_url": self.ollama_base_url,
            "use_proxy_api": self.use_proxy_api,
            "proxy_api_key": self.proxy_api_key,
            "proxy_api_provider": self.proxy_api_provider,
            "model_name": self.ollama_model if not self.use_proxy_api else self.proxy_models.get(self.proxy_api_provider, "gpt-4o-mini")
        }
    
    def is_configured(self) -> bool:
        """Проверить, настроен ли анализатор"""
        if self.use_proxy_api:
            return bool(self.proxy_api_key and self.proxy_api_provider in self.proxy_models)
        else:
            return True  # Ollama не требует дополнительной настройки
    
    def get_available_providers(self) -> list:
        """Получить список доступных провайдеров"""
        providers = ["ollama"]
        if self.proxy_api_key:
            providers.extend(["openai", "anthropic", "gemini"])
        return providers
    
    def validate_config(self) -> Dict[str, str]:
        """Валидация конфигурации"""
        errors = {}
        
        if self.use_proxy_api:
            if not self.proxy_api_key:
                errors["proxy_api_key"] = "API ключ ProxyAPI не установлен"
            
            if self.proxy_api_provider not in self.proxy_models:
                errors["proxy_api_provider"] = f"Неподдерживаемый провайдер: {self.proxy_api_provider}"
        
        if self.max_image_size_mb <= 0:
            errors["max_image_size_mb"] = "Максимальный размер изображения должен быть больше 0"
        
        if self.analysis_timeout <= 0:
            errors["analysis_timeout"] = "Таймаут анализа должен быть больше 0"
        
        if self.temperature < 0 or self.temperature > 2:
            errors["temperature"] = "Температура должна быть от 0 до 2"
        
        if self.max_tokens <= 0:
            errors["max_tokens"] = "Максимальное количество токенов должно быть больше 0"
        
        return errors

# Глобальный экземпляр конфигурации
config = ImageAnalyzerConfig()
