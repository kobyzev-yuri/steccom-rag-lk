#!/usr/bin/env python3
"""
Простой тест SQL генерации с упрощенным промптом
"""

import sys
import os
import time
import requests
import json

def test_simple_sql():
    """Тест с упрощенным промптом"""
    print("🧮 Тест упрощенного SQL Assistant")
    print("=" * 50)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    # Упрощенный промпт
    simple_prompt = """Сгенерируй SQL запрос для получения трафика по компаниям за 2025 год помесячно.

Схема базы данных:
- billing_records: billing_date, usage_amount, agreement_id
- agreements: user_id, agreement_id  
- users: company, user_id
- service_types: name, unit

Нужен запрос для получения помесячного трафика по компаниям в 2025 году.
Отвечай только SQL запросом без объяснений."""

    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": simple_prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    print("📤 Отправляем упрощенный запрос...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Время ответа: {duration:.2f} секунд")
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Ответ получен:")
            print(content)
            
            if duration < 10:
                print(f"✅ Отлично! Быстрый ответ за {duration:.2f} секунд")
            elif duration < 30:
                print(f"⚠️  Приемлемо: {duration:.2f} секунд")
            else:
                print(f"❌ Медленно: {duration:.2f} секунд")
                
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса (>30 сек)")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def test_even_simpler():
    """Еще более простой тест"""
    print("\n🚀 Тест максимально простого запроса")
    print("=" * 50)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": "SELECT * FROM users LIMIT 5"}],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    print("📤 Отправляем простейший запрос...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=15)
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
        print("❌ Таймаут запроса (>15 сек)")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    print(f"🚀 Запуск простых тестов SQL - {time.strftime('%H:%M:%S')}")
    
    # Проверяем, что модель загружена
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            qwen_models = [m for m in models if 'qwen2.5:1.5b' in m.get('name', '')]
            if qwen_models:
                print("✅ Модель qwen2.5:1.5b доступна")
            else:
                print("⚠️  Модель qwen2.5:1.5b не найдена")
        else:
            print("❌ Ollama недоступен")
    except:
        print("❌ Не удается подключиться к Ollama")
    
    # Простейший тест
    test_even_simpler()
    
    # Упрощенный SQL тест
    test_simple_sql()
    
    print("\n✅ Тестирование завершено")
