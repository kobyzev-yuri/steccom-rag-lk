#!/usr/bin/env python3
"""
Тест новых функций AI Billing
"""

import requests
import time
import sys
from pathlib import Path

def test_ai_billing_accessibility():
    """Тест доступности AI Billing"""
    print("🧪 Тестирование AI Billing")
    print("=" * 50)
    
    # Проверяем доступность
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ AI Billing доступен на порту 8501")
        else:
            print(f"❌ AI Billing недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к AI Billing: {e}")
        return False
    
    return True

def test_prompt_files():
    """Тест наличия файлов промптов"""
    print("\n📝 Тестирование файлов промптов")
    print("-" * 30)
    
    prompt_files = [
        "resources/prompts/sql_prompt.txt",
        "resources/prompts/rag_prompt.txt", 
        "resources/prompts/assistant_prompt.txt"
    ]
    
    all_exist = True
    for file_path in prompt_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} не найден")
            all_exist = False
    
    return all_exist

def test_prompt_manager_module():
    """Тест модуля управления промптами"""
    print("\n🔧 Тестирование модуля PromptManager")
    print("-" * 40)
    
    try:
        sys.path.append(str(Path(__file__).parent))
        from modules.ui.prompt_manager import PromptManager
        
        # Создаем экземпляр
        pm = PromptManager()
        print("✅ PromptManager создан успешно")
        
        # Проверяем загрузку промптов
        prompts = pm._load_all_prompts()
        print(f"✅ Загружено промптов: {len(prompts)}")
        
        for name in prompts:
            print(f"  - {name}: {len(prompts[name])} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка PromptManager: {e}")
        return False

def test_documentation_link():
    """Тест ссылки на документацию"""
    print("\n📚 Тестирование ссылки на документацию")
    print("-" * 40)
    
    # Проверяем наличие README
    readme_path = Path("ai_billing/README.md")
    if readme_path.exists():
        print("✅ README.md AI Billing найден")
        
        # Проверяем содержимое
        content = readme_path.read_text(encoding='utf-8')
        if "AI Billing System" in content:
            print("✅ Содержимое README корректно")
        else:
            print("❌ Содержимое README некорректно")
            return False
    else:
        print("❌ README.md AI Billing не найден")
        return False
    
    return True

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования AI Billing")
    print("=" * 60)
    
    tests = [
        ("Доступность AI Billing", test_ai_billing_accessibility),
        ("Файлы промптов", test_prompt_files),
        ("Модуль PromptManager", test_prompt_manager_module),
        ("Ссылка на документацию", test_documentation_link)
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
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ AI BILLING")
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
        print("🎉 Все тесты AI Billing пройдены успешно!")
        return True
    else:
        print("⚠️ Некоторые тесты AI Billing провалены")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
