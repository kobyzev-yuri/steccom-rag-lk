#!/usr/bin/env python3
"""
Запуск FastAPI сервера для СТЭККОМ Billing API
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Убеждаемся, что мы в правильной директории
    api_dir = Path(__file__).parent
    os.chdir(api_dir.parent)  # Переходим в корень проекта
    
    print("🚀 Запуск СТЭККОМ Billing API...")
    print("📖 Документация: http://localhost:8000/docs")
    print("🔧 ReDoc: http://localhost:8000/redoc")
    print("💚 Health check: http://localhost:8000/health")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменениях
        log_level="info"
    )
