"""
Configuration settings for KB Admin
Настройки конфигурации для системы управления базами знаний
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# ----------------------------
# Base paths (project defaults)
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR.parent / "data"  # Используем data из основного проекта
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
KNOWLEDGE_BASES_DIR = DATA_DIR / "knowledge_bases"
LOGS_DIR = BASE_DIR / "logs"

# Дополняем: архив и обработанные (ранее отсутствовали в этом файле)
ARCHIVE_DIR = DATA_DIR / "archive"
PROCESSED_DIR = DATA_DIR / "processed"

# ----------------------------
# Helpers
# ----------------------------
def _b(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"

def _i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _dir_with_env(env_name_primary: str, env_name_fallback: str, default_path: Path) -> Path:
    """
    Возвращает директорию с учетом ENV переопределений, с безопасным откатом на дефолт.
    Правила:
      - если ENV задан и директория доступна (или может быть создана) — используем её
      - иначе — дефолтный путь
    """
    raw = os.getenv(env_name_primary) or os.getenv(env_name_fallback)
    if not raw:
        return default_path
    candidate = Path(raw)
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        # Проверим базовые права (rwx для процесса)
        if os.access(candidate, os.R_OK | os.W_OK | os.X_OK):
            return candidate
    except Exception:
        pass
    return default_path

# --------------------------------------
# Apply ENV overrides for important dirs
# --------------------------------------
# Опционально форсим локальные директории (игнорируем внешние монтирования)
_FORCE_LOCAL_DIRS = os.getenv("STEC_FORCE_LOCAL_DIRS", "false").lower() == "true"

if not _FORCE_LOCAL_DIRS:
    UPLOAD_DIR = _dir_with_env("STEC_UPLOAD_DIR", "UPLOAD_DIR", UPLOAD_DIR)
    ARCHIVE_DIR = _dir_with_env("STEC_ARCHIVE_DIR", "ARCHIVE_DIR", ARCHIVE_DIR)
    PROCESSED_DIR = _dir_with_env("STEC_PROCESSED_DIR", "PROCESSED_DIR", PROCESSED_DIR)

# ----------------------------
# Database (shared with AI billing)
# ----------------------------
DATABASE_PATH = BASE_DIR / "kbs.db"

# ----------------------------
# RAG settings (existing)
# ----------------------------
RAG_SETTINGS = {
    "chunk_size": 600,
    "chunk_overlap": 100,
    "max_context_docs": 5,
    "similarity_threshold": 0.7,
    "embedding_model": "intfloat/multilingual-e5-base",
    "embedding_provider": "huggingface"
}

# ----------------------------
# Model configurations (existing)
# ----------------------------
MODEL_CONFIGS = {
    "gpt-4o": {
        "provider": "proxyapi",
        "temperature": 0.0,
        "max_tokens": 2000,
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01
    },
    "gpt-3.5-turbo": {
        "provider": "proxyapi", 
        "temperature": 0.0,
        "max_tokens": 1500,
        "cost_per_1k_input": 0.001,
        "cost_per_1k_output": 0.002
    },
    "qwen2.5:1.5b": {
        "provider": "ollama",
        "temperature": 0.0,
        "max_tokens": 1000,
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0
    },
    "gemini-2.0-flash": {
        "provider": "proxyapi",
        "temperature": 0.1,
        "max_tokens": 2000,
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "vision_capable": True,
        "ocr_capable": True
    },
    "gemini-1.5-pro": {
        "provider": "proxyapi",
        "temperature": 0.1,
        "max_tokens": 4000,
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
        "vision_capable": True,
        "ocr_capable": True
    }
}

# ----------------------------
# Default model choices (NEW)
# ----------------------------
MODEL_DEFAULTS = {
    "VISION_MODEL": os.getenv("STEC_VISION_MODEL", "gemini-2.0-flash"),
    "CHAT_MODEL": os.getenv("STEC_CHAT_MODEL", "qwen3:8b"),
    "OCR_MODEL": os.getenv("STEC_OCR_MODEL", "gemini-2.0-flash"),
    "DOCUMENT_ANALYSIS_MODEL": os.getenv("STEC_DOCUMENT_ANALYSIS_MODEL", "gemini-1.5-pro"),
}

# ----------------------------
# File upload settings (existing)
# ----------------------------
UPLOAD_SETTINGS = {
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "allowed_extensions": ['.pdf', '.txt', '.docx', '.json'],
    "temp_dir": BASE_DIR / "temp"
}

# ----------------------------
# Knowledge base categories (existing)
# ----------------------------
KB_CATEGORIES = [
    "Технические регламенты",
    "Пользовательские инструкции", 
    "Политики безопасности",
    "Процедуры биллинга",
    "Техническая поддержка",
    "Документация API",
    "FAQ",
    "Правовые документы",
    "Другое"
]

# ----------------------------
# Chunk optimization presets (existing)
# ----------------------------
CHUNK_PRESETS = {
    "regulations": {
        "chunk_size": 600,
        "chunk_overlap": 100,
        "separators": ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
        "description": "Регламенты и техническая документация"
    },
    "manuals": {
        "chunk_size": 800,
        "chunk_overlap": 150,
        "separators": ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        "description": "Руководства пользователя"
    },
    "faq": {
        "chunk_size": 400,
        "chunk_overlap": 80,
        "separators": ["\n\n", "\n", "? ", ". ", " ", ""],
        "description": "Часто задаваемые вопросы"
    },
    "api_docs": {
        "chunk_size": 700,
        "chunk_overlap": 120,
        "separators": ["\n\n", "\n", "```", "## ", "# ", ". ", " ", ""],
        "description": "Документация API"
    },
    "legal": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "separators": ["\n\n", "\n", "Статья ", "Пункт ", ". ", " ", ""],
        "description": "Правовые документы"
    }
}

# ----------------------------
# Testing settings (existing)
# ----------------------------
TESTING_SETTINGS = {
    "default_questions_per_category": 5,
    "min_accuracy_threshold": 0.7,
    "min_completeness_threshold": 0.6,
    "min_relevance_threshold": 0.8,
    "test_timeout": 30,  # seconds
    "max_retries": 3
}

# ----------------------------
# MediaWiki integration (existing)
# ----------------------------
MEDIAWIKI_SETTINGS = {
    "base_url": "http://localhost:8080",
    "api_endpoint": "/api.php",
    "username": "admin",
    "password": "Admin123456789",
    "namespace": 0,
    "timeout": 30
}

# ----------------------------
# Logging settings (existing)
# ----------------------------
LOGGING_SETTINGS = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "kb_admin.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# ----------------------------
# UI settings (existing)
# ----------------------------
UI_SETTINGS = {
    "page_title": "KB Admin - Управление базами знаний",
    "page_icon": "🧠",
    "layout": "wide",
    "sidebar_state": "expanded",
    "theme": "light"
}

# ----------------------------
# Performance settings (existing)
# ----------------------------
PERFORMANCE_SETTINGS = {
    "cache_ttl": 3600,  # 1 hour
    "max_concurrent_requests": 5,
    "request_timeout": 30,
    "enable_caching": True
}

# ----------------------------
# Security settings (existing)
# ----------------------------
SECURITY_SETTINGS = {
    "require_authentication": False,  # Пока отключено
    "allowed_ips": [],  # Пустой список = все IP разрешены
    "session_timeout": 3600,  # 1 hour
    "max_login_attempts": 5
}

# ----------------------------
# DOCX processing settings (NEW)
# ----------------------------
DOCX_PROCESSING = {
    "ENABLE_AI_CLEANING_TEXT": _b("STEC_ENABLE_AI_CLEANING_TEXT", "false"),
    "ABSTRACT_ENABLED": _b("STEC_DOCX_ABSTRACT_ENABLED", "true"),
    "QA_SKIP_ABSTRACT": _b("STEC_DOCX_QA_SKIP_ABSTRACT", "true"),
    "HUGE_MB_THRESHOLD": _i("STEC_DOCX_HUGE_MB_THRESHOLD", 20),
    "HUGE_CHARS_THRESHOLD": _i("STEC_DOCX_HUGE_CHARS_THRESHOLD", 100000),
}

# ----------------------------
# Unified SETTINGS for UI Settings page (NEW)
# ----------------------------
SETTINGS: Dict[str, Any] = {
    "paths": {
        "UPLOAD_DIR": str(UPLOAD_DIR),
        "ARCHIVE_DIR": str(ARCHIVE_DIR),
        "PROCESSED_DIR": str(PROCESSED_DIR),
        "EXPORT_DIR": str(EXPORT_DIR),
        "KNOWLEDGE_BASES_DIR": str(KNOWLEDGE_BASES_DIR),
        "LOGS_DIR": str(LOGS_DIR),
        "DATA_DIR": str(DATA_DIR),
    },
    "models": MODEL_DEFAULTS,
    "docx": DOCX_PROCESSING,
    "rag": RAG_SETTINGS,
    "ui": UI_SETTINGS,
    "performance": PERFORMANCE_SETTINGS,
    "security": SECURITY_SETTINGS,
    "logging": LOGGING_SETTINGS,
    "upload": {
        **UPLOAD_SETTINGS,
        "temp_dir": str(UPLOAD_SETTINGS["temp_dir"]),
    },
}

# ----------------------------
# Access helpers (existing)
# ----------------------------
def get_setting(category: str, key: str, default: Any = None) -> Any:
    """Получение настройки по категории и ключу"""
    settings_map = {
        "rag": RAG_SETTINGS,
        "models": MODEL_CONFIGS,
        "upload": UPLOAD_SETTINGS,
        "chunks": CHUNK_PRESETS,
        "testing": TESTING_SETTINGS,
        "mediawiki": MEDIAWIKI_SETTINGS,
        "logging": LOGGING_SETTINGS,
        "ui": UI_SETTINGS,
        "performance": PERFORMANCE_SETTINGS,
        "security": SECURITY_SETTINGS
    }
    if category in settings_map:
        return settings_map[category].get(key, default)
    return default

def get_environment_variable(key: str, default: Any = None) -> Any:
    """Получение переменной окружения с fallback на настройки"""
    return os.getenv(key, default)

# ----------------------------
# Create directories if they don't exist
# ----------------------------
for directory in [DATA_DIR, UPLOAD_DIR, EXPORT_DIR, KNOWLEDGE_BASES_DIR, LOGS_DIR, ARCHIVE_DIR, PROCESSED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Validate configuration (existing)
# ----------------------------
def validate_config() -> List[str]:
    """Валидация конфигурации"""
    errors = []
    # Проверка путей
    if not DATA_DIR.exists():
        errors.append(f"Data directory does not exist: {DATA_DIR}")
    if not DATABASE_PATH.exists():
        errors.append(f"Database file does not exist: {DATABASE_PATH}")
    # Проверка настроек
    if RAG_SETTINGS["chunk_size"] <= 0:
        errors.append("Invalid chunk_size in RAG settings")
    if RAG_SETTINGS["chunk_overlap"] < 0:
        errors.append("Invalid chunk_overlap in RAG settings")
    return errors

# ----------------------------
# Init check
# ----------------------------
if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")