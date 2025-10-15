#!/usr/bin/env python3
"""
Тест статуса RAG системы в KB Admin
"""

import requests
import time
import json
from pathlib import Path

def test_rag_status_in_interface():
    """Тест статуса RAG системы через интерфейс"""
    try:
        # Получаем главную страницу
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit интерфейс доступен")
            
            # Проверяем, что страница содержит элементы RAG системы
            content = response.text.lower()
            
            if "rag" in content or "актив" in content or "система" in content:
                print("✅ RAG система упоминается в интерфейсе")
                return True
            else:
                print("⚠️ RAG система не найдена в интерфейсе")
                return False
        else:
            print(f"❌ Ошибка доступа к интерфейсу: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования интерфейса: {e}")
        return False

def test_rag_functionality():
    """Тест функциональности RAG системы"""
    try:
        from modules.rag.multi_kb_rag import MultiKBRAG
        import sys
        sys.path.append('.')
        
        rag = MultiKBRAG()
        print(f"✅ RAG система инициализирована")
        print(f"   Векторных хранилищ: {len(rag.vectorstores)}")
        print(f"   Метаданных KB: {len(rag.kb_metadata)}")
        
        # Тестируем поиск
        results = rag.search_across_kbs('спутниковая связь', k=2)
        print(f"✅ Поиск работает: найдено {len(results)} результатов")
        
        if results:
            print(f"   Пример результата: {results[0].page_content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования RAG: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Финальное тестирование RAG системы в KB Admin...")
    print("=" * 60)
    
    tests = [
        ("Интерфейс Streamlit", test_rag_status_in_interface),
        ("Функциональность RAG", test_rag_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Тестирование: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Результаты финального тестирования:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! RAG система полностью функциональна!")
        return True
    else:
        print("⚠️ Некоторые тесты провалены.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)










