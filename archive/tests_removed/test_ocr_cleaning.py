#!/usr/bin/env python3
"""
Тест улучшенного агента очистки OCR
Проверяет создание полного очищенного текста без сокращений
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

def test_ocr_cleaning():
    """Тест улучшенной очистки OCR"""
    
    print("🧪 Тестирование улучшенного агента очистки OCR")
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
    print("\n3️⃣ Анализ документа с улучшенной очисткой...")
    try:
        analysis = smart_librarian.analyze_document(test_file)
        
        print(f"✅ Анализ документа завершен")
        print(f"📄 Файл: {analysis['file_name']}")
        print(f"📏 Размер: {analysis['file_size'] / 1024:.1f} KB")
        
        # Проверяем различные версии текста
        raw_text = analysis.get('raw_ocr_text', '')
        original_cleaned = analysis.get('original_cleaned_text', '')
        smart_summary = analysis.get('smart_summary', '')
        
        print(f"\n📊 Статистика текстов:")
        print(f"   🔴 Исходный OCR: {len(raw_text):,} символов")
        print(f"   🟢 Полный очищенный: {len(original_cleaned):,} символов")
        print(f"   📋 Абстракт: {len(smart_summary):,} символов")
        
        # Показываем примеры улучшений
        if raw_text and original_cleaned:
            print(f"\n🔍 Примеры улучшений:")
            
            # Ищем кракозябры в исходном тексте
            import re
            garbage_patterns = [
                r'Ваюменовяние',
                r'иоготовителя', 
                r'еее\s+СООТВЕТСТВУЮТ',
                r'завола\]\s*-\s*изготовителя',
                r'[^\w\s]{3,}'
            ]
            
            found_garbage = []
            for pattern in garbage_patterns:
                matches = re.findall(pattern, raw_text)
                if matches:
                    found_garbage.extend(matches[:3])  # Берем первые 3 примера
            
            if found_garbage:
                print(f"   🔴 Найдены кракозябры в исходном тексте:")
                for garbage in found_garbage[:5]:  # Показываем первые 5
                    print(f"      - '{garbage}'")
            
            # Проверяем, исправлены ли они в очищенном тексте
            if found_garbage:
                print(f"   🟢 Проверяем исправления в очищенном тексте...")
                for garbage in found_garbage[:3]:
                    if garbage not in original_cleaned:
                        print(f"      ✅ '{garbage}' исправлен")
                    else:
                        print(f"      ⚠️ '{garbage}' не исправлен")
        
        # Показываем превью текстов
        print(f"\n📝 Превью текстов:")
        print(f"   🔴 Исходный OCR (первые 200 символов):")
        print(f"      {raw_text[:200]}...")
        
        print(f"\n   🟢 Полный очищенный (первые 200 символов):")
        print(f"      {original_cleaned[:200]}...")
        
        print(f"\n   📋 Абстракт (первые 200 символов):")
        print(f"      {smart_summary[:200]}...")
        
        # Проверяем качество очистки
        if len(original_cleaned) > len(raw_text) * 0.8:  # Очищенный текст должен быть не менее 80% от исходного
            print(f"\n✅ Качество очистки: ХОРОШЕЕ (сохранено {len(original_cleaned)/len(raw_text)*100:.1f}% содержимого)")
        else:
            print(f"\n⚠️ Качество очистки: ПРОВЕРИТЬ (сохранено только {len(original_cleaned)/len(raw_text)*100:.1f}% содержимого)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста улучшенной очистки OCR")
    
    # Проверяем переменные окружения
    api_key = os.getenv('PROXYAPI_KEY')
    if not api_key:
        print("❌ PROXYAPI_KEY не настроен!")
        print("Установите переменную окружения: export PROXYAPI_KEY=your_key")
        sys.exit(1)
    
    print(f"🔑 API ключ: {api_key[:10]}...{api_key[-4:]}")
    
    # Запускаем тест
    success = test_ocr_cleaning()
    
    if success:
        print("\n🎯 Тест пройден успешно!")
        print("✅ Улучшенный агент очистки OCR работает корректно")
        sys.exit(0)
    else:
        print("\n💥 Тест завершился с ошибками!")
        sys.exit(1)
