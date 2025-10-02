#!/usr/bin/env python3
"""
Тест сохранения документов в KB
Проверяет полную цепочку: анализ -> предложение KB -> сохранение
"""

import os
import sys
from pathlib import Path
import logging

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
from kb_admin.modules.documents.pdf_processor import PDFProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_kb_save_functionality():
    """Тест функциональности сохранения в KB"""
    
    print("🧪 Тестирование сохранения документов в KB")
    print("=" * 60)
    
    # 1. Инициализируем компоненты
    print("\n1️⃣ Инициализация компонентов...")
    try:
        kb_manager = KnowledgeBaseManager()
        pdf_processor = PDFProcessor()
        smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
        print("✅ Все компоненты инициализированы")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # 2. Ищем тестовый PDF файл
    print("\n2️⃣ Поиск тестового PDF файла...")
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
    
    # 3. Анализируем документ
    print("\n3️⃣ Анализ документа...")
    try:
        analysis = smart_librarian.analyze_document(test_file)
        
        print(f"✅ Анализ документа завершен")
        print(f"📄 Файл: {analysis['file_name']}")
        print(f"📏 Размер: {analysis['file_size'] / 1024:.1f} KB")
        print(f"🏷️ Категория: {analysis['category']}")
        
        # Проверяем наличие предложения KB
        if 'suggested_kb' in analysis:
            kb_suggestion = analysis['suggested_kb']
            print(f"\n🗂️ Предложение KB:")
            print(f"   📝 Название: {kb_suggestion.get('suggested_name', 'Не указано')}")
            print(f"   📂 Категория: {kb_suggestion.get('suggested_category', 'Не указано')}")
            print(f"   📄 Описание: {kb_suggestion.get('description', 'Не указано')}")
            print(f"   🎯 Уверенность: {kb_suggestion.get('confidence', 0):.1%}")
            
            # Проверяем возможность объединения
            merge_info = kb_suggestion.get('merge_with_existing', {})
            if merge_info.get('can_merge', False):
                print(f"   🔗 Можно объединить с KB ID {merge_info.get('existing_kb_id')}")
                print(f"   💭 Причина: {merge_info.get('merge_reason', 'Не указано')}")
            else:
                print(f"   🆕 Рекомендуется создать новую KB")
        else:
            print("⚠️ Предложение KB не создано")
        
        # Проверяем наличие всех необходимых данных для сохранения
        required_fields = ['smart_summary', 'original_cleaned_text', 'images']
        missing_fields = []
        
        for field in required_fields:
            if field not in analysis or not analysis[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️ Отсутствуют поля для сохранения: {', '.join(missing_fields)}")
        else:
            print(f"✅ Все необходимые поля для сохранения присутствуют")
            
            # Показываем статистику данных
            print(f"\n📊 Статистика данных для сохранения:")
            print(f"   📋 Абстракт: {len(analysis.get('smart_summary', ''))} символов")
            print(f"   📄 Полный текст: {len(analysis.get('original_cleaned_text', ''))} символов")
            print(f"   🖼️ Изображений: {len(analysis.get('images', []))}")
            
            if analysis.get('images'):
                for i, img in enumerate(analysis['images']):
                    print(f"      📷 {i+1}. {img.get('image_name', 'Неизвестно')}")
                    if img.get('description'):
                        print(f"         📝 Описание Gemini: {len(img['description'])} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False

def test_kb_creation():
    """Тест создания KB"""
    
    print("\n4️⃣ Тест создания KB...")
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Получаем список существующих KB
        existing_kbs = kb_manager.get_knowledge_bases(active_only=True)
        print(f"📚 Существующих KB: {len(existing_kbs)}")
        
        for kb in existing_kbs[:3]:  # Показываем первые 3
            print(f"   - ID {kb['id']}: {kb['name']} ({kb['category']})")
        
        # Тестируем создание новой KB
        test_kb_name = "Тестовая KB для проверки"
        test_kb_category = "Тестовые документы"
        test_kb_description = "База знаний для тестирования функциональности"
        
        print(f"\n🧪 Создание тестовой KB...")
        kb_id = kb_manager.create_knowledge_base(
            name=test_kb_name,
            description=test_kb_description,
            category=test_kb_category,
            created_by="Test Script"
        )
        
        print(f"✅ KB создана с ID: {kb_id}")
        
        # Проверяем, что KB создалась
        created_kb = kb_manager.get_knowledge_base(kb_id)
        if created_kb:
            print(f"✅ KB успешно создана: {created_kb['name']}")
            
            # Удаляем тестовую KB
            if kb_manager.delete_knowledge_base(kb_id):
                print(f"🗑️ Тестовая KB удалена")
            else:
                print(f"⚠️ Не удалось удалить тестовую KB")
        else:
            print(f"❌ Не удалось получить созданную KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования KB: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста сохранения в KB")
    
    # Проверяем переменные окружения
    api_key = os.getenv('PROXYAPI_KEY')
    if not api_key:
        print("❌ PROXYAPI_KEY не настроен!")
        print("Установите переменную окружения: export PROXYAPI_KEY=your_key")
        sys.exit(1)
    
    print(f"🔑 API ключ: {api_key[:10]}...{api_key[-4:]}")
    
    # Запускаем тесты
    success1 = test_kb_save_functionality()
    success2 = test_kb_creation()
    
    if success1 and success2:
        print("\n🎯 Все тесты пройдены успешно!")
        print("✅ Функциональность сохранения в KB работает корректно")
        sys.exit(0)
    else:
        print("\n💥 Тесты завершились с ошибками!")
        sys.exit(1)
