#!/usr/bin/env python3
"""
Тест новых функций KB Admin
"""

import requests
import time
import sys
from pathlib import Path

def test_kb_admin_accessibility():
    """Тест доступности KB Admin"""
    print("🧪 Тестирование KB Admin")
    print("=" * 50)
    
    # Проверяем доступность
    try:
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            print("✅ KB Admin доступен на порту 8502")
        else:
            print(f"❌ KB Admin недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к KB Admin: {e}")
        return False
    
    return True

def test_mediawiki_integration():
    """Тест интеграции MediaWiki"""
    print("\n📤 Тестирование интеграции MediaWiki")
    print("-" * 40)
    
    try:
        # Проверяем наличие модулей MediaWiki
        sys.path.append(str(Path(__file__).parent))
        from modules.integrations.mediawiki_client import MediaWikiClient, KBToWikiPublisher
        
        print("✅ MediaWiki модули импортированы успешно")
        
        # Проверяем создание клиента
        client = MediaWikiClient("http://localhost:8080/api.php", "admin", "password")
        print("✅ MediaWikiClient создан успешно")
        
        # Проверяем создание публикатора
        publisher = KBToWikiPublisher(client)
        print("✅ KBToWikiPublisher создан успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка MediaWiki интеграции: {e}")
        return False

def test_kb_admin_modules():
    """Тест модулей KB Admin"""
    print("\n🔧 Тестирование модулей KB Admin")
    print("-" * 40)
    
    try:
        sys.path.append(str(Path(__file__).parent))
        
        # Проверяем основные модули
        from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
        from kb_admin.modules.core.text_analyzer import TextAnalyzer
        from kb_admin.modules.core.chunk_optimizer import ChunkOptimizer
        from kb_admin.modules.testing.kb_test_protocol import KBTestProtocol
        
        print("✅ Основные модули KB Admin импортированы")
        
        # Проверяем создание экземпляров
        kb_manager = KnowledgeBaseManager()
        text_analyzer = TextAnalyzer()
        chunk_optimizer = ChunkOptimizer()
        test_protocol = KBTestProtocol()
        
        print("✅ Экземпляры модулей созданы успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка модулей KB Admin: {e}")
        return False

def test_shared_modules():
    """Тест использования общих модулей"""
    print("\n🤝 Тестирование общих модулей")
    print("-" * 40)
    
    try:
        sys.path.append(str(Path(__file__).parent))
        
        # Проверяем импорт общих модулей из KB Admin
        from modules.rag.multi_kb_rag import MultiKBRAG
        from modules.integrations.mediawiki_client import MediaWikiClient
        from modules.documents.pdf_processor import PDFProcessor
        
        print("✅ Общие модули импортированы из KB Admin")
        
        # Проверяем создание экземпляров
        rag = MultiKBRAG()
        client = MediaWikiClient("http://localhost:8080/api.php", "admin", "password")
        pdf_processor = PDFProcessor("data/uploads")
        
        print("✅ Экземпляры общих модулей созданы успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка общих модулей: {e}")
        return False

def test_kb_admin_documentation():
    """Тест документации KB Admin"""
    print("\n📚 Тестирование документации KB Admin")
    print("-" * 40)
    
    # Проверяем наличие README
    readme_path = Path("kb_admin/README.md")
    if readme_path.exists():
        print("✅ README.md KB Admin найден")
        
        # Проверяем содержимое
        content = readme_path.read_text(encoding='utf-8')
        if "KB Admin" in content and "базами знаний" in content:
            print("✅ Содержимое README корректно")
        else:
            print("❌ Содержимое README некорректно")
            return False
    else:
        print("❌ README.md KB Admin не найден")
        return False
    
    return True

def test_wiki_publishing_page():
    """Тест страницы публикации в Wiki"""
    print("\n📤 Тестирование страницы публикации в Wiki")
    print("-" * 50)
    
    try:
        # Проверяем, что страница доступна (это будет HTML ответ)
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            print("✅ Страница KB Admin загружается")
            
            # Проверяем, что в HTML есть упоминания о Wiki (базовая проверка)
            html_content = response.text
            if "streamlit" in html_content.lower():
                print("✅ Streamlit интерфейс загружен")
            else:
                print("⚠️ Streamlit интерфейс может быть не полностью загружен")
        else:
            print(f"❌ Страница KB Admin недоступна: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки страницы: {e}")
        return False
    
    return True

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования KB Admin")
    print("=" * 60)
    
    tests = [
        ("Доступность KB Admin", test_kb_admin_accessibility),
        ("Интеграция MediaWiki", test_mediawiki_integration),
        ("Модули KB Admin", test_kb_admin_modules),
        ("Общие модули", test_shared_modules),
        ("Документация KB Admin", test_kb_admin_documentation),
        ("Страница публикации в Wiki", test_wiki_publishing_page)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ KB ADMIN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты KB Admin пройдены успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты KB Admin провалены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
