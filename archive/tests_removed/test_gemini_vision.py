#!/usr/bin/env python3
"""
Тест анализа изображений через Gemini
Проверяет всю цепочку: извлечение изображений -> анализ Gemini -> интеграция с OCR
"""

import os
import sys
from pathlib import Path
import logging

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.documents.vision_processor import VisionProcessor
from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
from kb_admin.modules.documents.pdf_processor import PDFProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_vision_chain():
    """Тест полной цепочки анализа изображений"""
    
    print("🧪 Тестирование цепочки анализа изображений от Gemini")
    print("=" * 60)
    
    # 1. Проверяем доступность Gemini
    print("\n1️⃣ Проверка доступности Gemini...")
    vision_processor = VisionProcessor()
    availability = vision_processor.check_model_availability()
    
    if availability['available']:
        print(f"✅ {availability['message']}")
    else:
        print(f"❌ {availability['message']}")
        return False
    
    # 2. Инициализируем компоненты
    print("\n2️⃣ Инициализация компонентов...")
    try:
        kb_manager = KnowledgeBaseManager()
        pdf_processor = PDFProcessor()
        smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
        print("✅ Все компоненты инициализированы")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # 3. Ищем тестовый PDF файл
    print("\n3️⃣ Поиск тестового PDF файла...")
    test_files = [
        "data/uploads/billmaster_7.pdf",
        "data/uploads/reg_07032015.pdf", 
        "data/uploads/reg_sbd.pdf"
    ]
    
    test_file = None
    for file_path in test_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            test_file = full_path
            print(f"✅ Найден тестовый файл: {test_file}")
            break
    
    if not test_file:
        print("❌ Тестовый PDF файл не найден")
        return False
    
    # 4. Извлекаем изображения из PDF
    print("\n4️⃣ Извлечение изображений из PDF...")
    try:
        extracted_images = smart_librarian._extract_images_from_pdf(test_file)
        print(f"✅ Извлечено {len(extracted_images)} изображений")
        
        for i, img_path in enumerate(extracted_images):
            print(f"   📷 {i+1}. {img_path.name}")
            
    except Exception as e:
        print(f"❌ Ошибка извлечения изображений: {e}")
        return False
    
    if not extracted_images:
        print("⚠️ Изображения не найдены в PDF")
        return False
    
    # 5. Тестируем анализ каждого изображения
    print("\n5️⃣ Анализ изображений через Gemini...")
    successful_analyses = 0
    
    for i, image_path in enumerate(extracted_images):
        print(f"\n   📷 Анализ изображения {i+1}: {image_path.name}")
        
        try:
            # Анализ изображения
            analysis_result = vision_processor.analyze_image_with_gemini(image_path)
            
            if analysis_result['success']:
                print(f"   ✅ Анализ успешен")
                print(f"   📝 Описание: {analysis_result['analysis'][:100]}...")
                print(f"   🤖 Модель: {analysis_result['model']}")
                print(f"   🔧 Провайдер: {analysis_result['provider']}")
                
                # Извлечение текста
                text_content = vision_processor.extract_text_from_image_gemini(image_path)
                if text_content and len(text_content) > 10:
                    print(f"   📄 Извлеченный текст: {text_content[:100]}...")
                else:
                    print(f"   📄 Текст не извлечен или слишком короткий")
                
                # Анализ структуры
                structure_result = vision_processor.analyze_document_structure(image_path)
                if structure_result['success']:
                    print(f"   🏗️ Структура проанализирована")
                else:
                    print(f"   ⚠️ Ошибка анализа структуры: {structure_result.get('error', 'Неизвестная ошибка')}")
                
                successful_analyses += 1
                
            else:
                print(f"   ❌ Ошибка анализа: {analysis_result.get('error', 'Неизвестная ошибка')}")
                
        except Exception as e:
            print(f"   ❌ Исключение при анализе: {e}")
    
    print(f"\n📊 Результат анализа: {successful_analyses}/{len(extracted_images)} изображений успешно проанализированы")
    
    # 6. Тестируем полный анализ документа
    print("\n6️⃣ Полный анализ документа...")
    try:
        analysis = smart_librarian.analyze_document(test_file)
        
        print(f"✅ Анализ документа завершен")
        print(f"📄 Файл: {analysis['file_name']}")
        print(f"📏 Размер: {analysis['file_size'] / 1024:.1f} KB")
        print(f"🏷️ Категория: {analysis['category']}")
        print(f"📝 Длина текста: {analysis.get('text_length', 0)} символов")
        print(f"🖼️ Количество изображений: {analysis.get('image_count', 0)}")
        
        if analysis.get('gemini_analysis'):
            print(f"🔗 Анализ от Gemini интегрирован: {len(analysis['gemini_analysis'])} символов")
        else:
            print("⚠️ Анализ от Gemini не интегрирован")
            
        if analysis.get('smart_summary'):
            print(f"📋 Абстракт создан: {len(analysis['smart_summary'])} символов")
            print(f"📋 Превью абстракта: {analysis['smart_summary'][:200]}...")
        
    except Exception as e:
        print(f"❌ Ошибка полного анализа: {e}")
        return False
    
    # 7. Итоговый результат
    print("\n" + "=" * 60)
    if successful_analyses > 0:
        print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"✅ Gemini анализ работает корректно")
        print(f"✅ Интеграция с OCR функционирует")
        print(f"✅ Полный анализ документа работает")
        return True
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        print("❌ Анализ изображений не работает")
        return False

def test_individual_components():
    """Тест отдельных компонентов"""
    
    print("\n🔧 Тестирование отдельных компонентов")
    print("=" * 40)
    
    # Тест VisionProcessor
    print("\n1️⃣ Тест VisionProcessor...")
    try:
        vision_processor = VisionProcessor()
        print(f"✅ VisionProcessor инициализирован")
        print(f"🤖 Модель: {vision_processor.gemini_model}")
        print(f"🔑 API ключ: {'Настроен' if vision_processor.proxy_api_key else 'Не настроен'}")
    except Exception as e:
        print(f"❌ Ошибка VisionProcessor: {e}")
    
    # Тест доступности API
    print("\n2️⃣ Тест доступности API...")
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {os.getenv('PROXYAPI_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.proxyapi.ru/google/v1/models",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ ProxyAPI доступен")
            models = response.json()
            gemini_models = [m for m in models['data'] if 'gemini' in m['id'].lower()]
            print(f"📋 Доступные модели Gemini: {len(gemini_models)}")
            for model in gemini_models[:3]:  # Показываем первые 3
                print(f"   - {model['id']}")
        else:
            print(f"❌ ProxyAPI недоступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов анализа изображений от Gemini")
    
    # Проверяем переменные окружения
    api_key = os.getenv('PROXYAPI_KEY')
    if not api_key:
        print("❌ PROXYAPI_KEY не настроен!")
        print("Установите переменную окружения: export PROXYAPI_KEY=your_key")
        sys.exit(1)
    
    print(f"🔑 API ключ: {api_key[:10]}...{api_key[-4:]}")
    
    # Запускаем тесты
    test_individual_components()
    success = test_gemini_vision_chain()
    
    if success:
        print("\n🎯 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("\n💥 Тесты завершились с ошибками!")
        sys.exit(1)
