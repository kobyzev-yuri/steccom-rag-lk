#!/usr/bin/env python3
"""
Тест SQL Assistant для проверки генерации SQL запросов
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.core.rag import SQLAgent

def test_sql_assistant():
    """Тестирование SQL Assistant"""
    print("🧮 Тестирование SQL Assistant")
    print("=" * 50)
    
    # Инициализируем SQL Agent
    try:
        sql_agent = SQLAgent()
        print("✅ SQL Agent инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации SQL Agent: {e}")
        return
    
    # Тестовые вопросы
    test_questions = [
        "Отчет о трафике по компаниям в 2025 году помесячно",
        "Покажи статистику трафика за последний месяц",
        "Список устройств по компаниям",
        "SBD трафик за январь 2025"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Тест {i}: {question}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Генерируем SQL запрос
            sql_query = sql_agent.generate_sql_query(question)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏱️  Время генерации: {duration:.2f} секунд")
            print(f"📊 Сгенерированный SQL:")
            print(sql_query)
            
            if duration > 30:
                print(f"⚠️  ВНИМАНИЕ: Генерация заняла {duration:.2f} секунд (>30 сек)")
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ Ошибка генерации SQL: {e}")
            print(f"⏱️  Время до ошибки: {duration:.2f} секунд")
        
        print()

def test_ollama_direct():
    """Прямой тест Ollama API"""
    print("\n🔧 Прямой тест Ollama API")
    print("=" * 50)
    
    import requests
    import json
    
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [
            {"role": "user", "content": "Сгенерируй простой SQL запрос для получения всех записей из таблицы users"}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    print("📤 Отправляем запрос к Ollama...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Время ответа: {duration:.2f} секунд")
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Ответ получен:")
            print(content)
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса (>60 сек)")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    print(f"🚀 Запуск тестов SQL Assistant - {datetime.now()}")
    
    # Тест прямого API
    test_ollama_direct()
    
    # Тест SQL Assistant
    test_sql_assistant()
    
    print("\n✅ Тестирование завершено")
