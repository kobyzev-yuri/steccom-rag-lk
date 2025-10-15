#!/usr/bin/env python3
"""
Тест функциональности KB Admin приложения
"""

import requests
import time
import json
from pathlib import Path

def test_streamlit_app():
    """Тест доступности Streamlit приложения"""
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit приложение доступно")
            return True
        else:
            print(f"❌ Streamlit приложение недоступно: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Streamlit: {e}")
        return False

def test_mediawiki_api():
    """Тест доступности MediaWiki API"""
    try:
        response = requests.get("http://localhost:8080/api.php?action=query&meta=tokens&type=login&format=json", timeout=10)
        if response.status_code == 200:
            print("✅ MediaWiki API доступен")
            return True
        else:
            print(f"❌ MediaWiki API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к MediaWiki: {e}")
        return False

def test_ollama_connection():
    """Тест подключения к Ollama"""
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ollama доступен")
            lines = result.stdout.strip().split('\n')
            print(f"   Доступные модели: {len(lines) - 1}")
            return True
        else:
            print(f"❌ Ollama недоступен: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        return False

def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        import sqlite3
        db_path = Path(__file__).parent / "kbs.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_bases")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ База данных доступна, найдено {count} баз знаний")
            return True
        else:
            print("❌ База данных не найдена")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_kb_admin_modules():
    """Тест импорта модулей KB Admin"""
    try:
        import sys
        sys.path.append(str(Path(__file__).parent))
        
        from modules.core.knowledge_manager import KnowledgeBaseManager
        from modules.core.text_analyzer import TextAnalyzer
        from modules.rag.multi_kb_rag import MultiKBRAG
        
        print("✅ Основные модули KB Admin импортируются успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование KB Admin приложения...")
    print("=" * 50)
    
    tests = [
        ("Streamlit приложение", test_streamlit_app),
        ("MediaWiki API", test_mediawiki_api),
        ("Ollama", test_ollama_connection),
        ("База данных", test_database_connection),
        ("Модули KB Admin", test_kb_admin_modules),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\\n🔍 Тестирование: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте конфигурацию.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
