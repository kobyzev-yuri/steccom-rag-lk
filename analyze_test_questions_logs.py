#!/usr/bin/env python3
"""
Скрипт для анализа логов генерации тестовых вопросов
"""

import re
import sys
from pathlib import Path

def analyze_logs(log_file_path: str):
    """Анализирует логи генерации тестовых вопросов"""
    
    if not Path(log_file_path).exists():
        print(f"❌ Файл логов не найден: {log_file_path}")
        return
    
    print("🔍 Анализ логов генерации тестовых вопросов")
    print("=" * 60)
    
    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем все записи о генерации тестовых вопросов
    test_questions_pattern = r'Генерируем тестовые вопросы для проверки релевантности'
    test_questions_matches = re.findall(test_questions_pattern, content)
    
    if not test_questions_matches:
        print("❌ Не найдено записей о генерации тестовых вопросов")
        return
    
    print(f"✅ Найдено {len(test_questions_matches)} записей о генерации тестовых вопросов")
    
    # Ищем размер документа
    doc_size_pattern = r'Размер документа для анализа: (\d+) символов'
    doc_size_matches = re.findall(doc_size_pattern, content)
    if doc_size_matches:
        print(f"📄 Размер документа: {doc_size_matches[-1]} символов")
    
    # Ищем название документа
    doc_name_pattern = r'Название документа: (.+)'
    doc_name_matches = re.findall(doc_name_pattern, content)
    if doc_name_matches:
        print(f"📄 Название документа: {doc_name_matches[-1]}")
    
    # Ищем категорию документа
    doc_category_pattern = r'Категория документа: (.+)'
    doc_category_matches = re.findall(doc_category_pattern, content)
    if doc_category_matches:
        print(f"📄 Категория документа: {doc_category_matches[-1]}")
    
    # Ищем информацию о модели
    model_type_pattern = r'Тип модели: (.+)'
    model_type_matches = re.findall(model_type_pattern, content)
    if model_type_matches:
        print(f"🤖 Тип модели: {model_type_matches[-1]}")
    
    model_name_pattern = r'Модель: (.+)'
    model_name_matches = re.findall(model_name_pattern, content)
    if model_name_matches:
        print(f"🤖 Модель: {model_name_matches[-1]}")
    
    # Ищем ответ модели
    response_pattern = r'Ответ модели: (.+?)(?=\n|$)'
    response_matches = re.findall(response_pattern, content, re.DOTALL)
    if response_matches:
        print(f"🤖 Ответ модели (первые 200 символов): {response_matches[-1][:200]}...")
    
    # Ищем ошибки
    error_pattern = r'❌ Ошибка при вызове локальной модели: (.+)'
    error_matches = re.findall(error_pattern, content)
    if error_matches:
        print(f"❌ Ошибка модели: {error_matches[-1]}")
    
    json_error_pattern = r'Ошибка парсинга JSON ответа: (.+)'
    json_error_matches = re.findall(json_error_pattern, content)
    if json_error_matches:
        print(f"❌ Ошибка парсинга JSON: {json_error_matches[-1]}")
    
    # Ищем использование базовых вопросов
    basic_questions_pattern = r'⚠️ Используем базовые вопросы для категории: (.+)'
    basic_questions_matches = re.findall(basic_questions_pattern, content)
    if basic_questions_matches:
        print(f"⚠️ Использованы базовые вопросы для категории: {basic_questions_matches[-1]}")
    
    # Ищем успешную генерацию
    success_pattern = r'✅ Сгенерировано (\d+) тестовых вопросов через LLM'
    success_matches = re.findall(success_pattern, content)
    if success_matches:
        print(f"✅ Успешно сгенерировано {success_matches[-1]} вопросов через LLM")
    
    print("\n" + "=" * 60)
    print("📊 Сводка:")
    
    if success_matches:
        print("✅ Генерация через LLM: УСПЕШНО")
    elif basic_questions_matches:
        print("⚠️ Генерация через LLM: НЕУДАЧНО (использованы базовые вопросы)")
    else:
        print("❓ Статус генерации: НЕИЗВЕСТНО")
    
    if error_matches:
        print(f"❌ Ошибка модели: {error_matches[-1]}")
    
    if json_error_matches:
        print(f"❌ Ошибка парсинга JSON: {json_error_matches[-1]}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python analyze_test_questions_logs.py <путь_к_логам>")
        print("Пример: python analyze_test_questions_logs.py /var/log/kb_admin.log")
        sys.exit(1)
    
    log_file_path = sys.argv[1]
    analyze_logs(log_file_path)
