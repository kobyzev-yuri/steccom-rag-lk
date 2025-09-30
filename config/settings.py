"""
Configuration settings for Steccom Personal Cabinet
Настройки конфигурации для личного кабинета СТЭККОМ
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
KNOWLEDGE_BASES_DIR = DATA_DIR / "knowledge_bases"

# Database
DATABASE_PATH = BASE_DIR / "satellite_billing.db"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"

# Model configurations - общие настройки для всех агентов
MODELS = {
    # Текстовые модели
    "chat": "qwen3:8b",
    "sql": "qwen3:8b", 
    "embedding": "all-minilm",
    
    # Vision модели
    "vision": "llava-phi3:latest",
    
    # Специализированные модели
    "document_analysis": "qwen3:8b",
    "text_extraction": "qwen3:8b",
    "content_categorization": "qwen3:8b"
}

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_KEY = "ollama"

# RAG settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONTEXT_DOCS = 5

# File upload settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.docx']

# Knowledge base categories
KB_CATEGORIES = [
    "Технические регламенты",
    "Пользовательские инструкции", 
    "Политики безопасности",
    "Процедуры биллинга",
    "Техническая поддержка",
    "Документация API",
    "Другое"
]

# User roles
USER_ROLES = {
    'staff': 'Сотрудник',
    'user': 'Пользователь',
    'admin': 'Администратор'
}

# Create directories if they don't exist
for directory in [DATA_DIR, UPLOAD_DIR, EXPORT_DIR, KNOWLEDGE_BASES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
