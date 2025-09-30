#!/usr/bin/env python3
"""
Тест скорости SQL генерации с разными промптами
"""

import sys
import os
import time
import requests
import json

def test_simple_prompt():
    """Тест с очень простым промптом"""
    print("🚀 Тест 1: Простейший промпт")
    print("-" * 40)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": "Напиши SQL запрос: SELECT * FROM users"}],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=15)
        duration = time.time() - start_time
        
        print(f"⏱️  Время: {duration:.2f} сек")
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Ответ: {content[:100]}...")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_medium_prompt():
    """Тест со средним промптом"""
    print("\n📊 Тест 2: Средний промпт")
    print("-" * 40)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    prompt = """Сгенерируй SQL запрос для получения трафика по компаниям за 2025 год.

Таблицы:
- billing_records (billing_date, usage_amount, agreement_id)
- agreements (user_id, agreement_id)  
- users (company, user_id)

Нужен запрос для помесячного трафика по компаниям в 2025 году."""

    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 300
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        duration = time.time() - start_time
        
        print(f"⏱️  Время: {duration:.2f} сек")
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Ответ получен (длина: {len(content)} символов)")
            print(f"📝 SQL: {content[:200]}...")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_complex_prompt():
    """Тест со сложным промптом (как в реальной системе)"""
    print("\n🔥 Тест 3: Сложный промпт (как в системе)")
    print("-" * 40)
    
    url = "http://localhost:11434/v1/chat/completions"
    
    # Упрощенная версия реального промпта
    complex_prompt = """You are a SQLite expert for a satellite communications billing system. Generate a query for the following question: "Отчет о трафике по компаниям в 2025 году помесячно".

CRITICAL RULES:
1. NEVER modify the user's question
2. If user mentions specific year/month, filter by that period
3. For traffic totals, include service_types.name and service_types.unit in SELECT
4. Group by service_type to avoid mixing different services
5. Use strftime('%Y-%m', billing_date) for monthly grouping

Database Schema:
- billing_records: billing_date, usage_amount, agreement_id, service_type_id
- agreements: user_id, agreement_id  
- users: company, user_id
- service_types: name, unit, service_type_id

Generate SQL query for monthly traffic by companies in 2025."""

    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": complex_prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=60)
        duration = time.time() - start_time
        
        print(f"⏱️  Время: {duration:.2f} сек")
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Ответ получен (длина: {len(content)} символов)")
            print(f"📝 SQL: {content[:300]}...")
            
            if duration > 30:
                print(f"⚠️  МЕДЛЕННО: {duration:.2f} секунд")
            elif duration > 10:
                print(f"⚠️  Приемлемо: {duration:.2f} секунд")
            else:
                print(f"✅ Быстро: {duration:.2f} секунд")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_ollama_status():
    """Проверка статуса Ollama"""
    print("🔍 Проверка статуса Ollama")
    print("-" * 40)
    
    try:
        # Проверяем доступность
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama доступен, моделей: {len(models)}")
            
            # Ищем нашу модель
            qwen_models = [m for m in models if 'qwen2.5:1.5b' in m.get('name', '')]
            if qwen_models:
                model = qwen_models[0]
                size_gb = model.get('size', 0) / (1024**3)
                print(f"✅ Модель qwen2.5:1.5b найдена (размер: {size_gb:.1f} GB)")
            else:
                print("❌ Модель qwen2.5:1.5b не найдена")
        else:
            print("❌ Ollama недоступен")
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")

if __name__ == "__main__":
    print(f"🧮 Тест скорости SQL генерации - {time.strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Проверяем статус
    check_ollama_status()
    
    # Запускаем тесты по возрастанию сложности
    test_simple_prompt()
    test_medium_prompt()
    test_complex_prompt()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено")
    print("\n💡 Рекомендации:")
    print("- Если простой промпт работает быстро, проблема в сложности")
    print("- Если все медленно, проблема в модели или системе")
    print("- Если сложный промпт медленный, нужна оптимизация")
