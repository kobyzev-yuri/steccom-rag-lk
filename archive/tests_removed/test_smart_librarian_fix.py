#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления Умного библиотекаря
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
from kb_admin.modules.documents.pdf_processor import PDFProcessor

def test_smart_librarian_fix():
    """Тестирование исправления Умного библиотекаря"""
    print("🔧 Тестирование исправления Умного библиотекаря")
    print("=" * 60)
    
    # Инициализация
    kb_manager = KnowledgeBaseManager()
    pdf_processor = PDFProcessor("data/uploads")
    smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
    
    # Проверяем наличие тестового PDF
    test_pdf = Path("data/uploads/billmaster_7.pdf")
    if not test_pdf.exists():
        print(f"❌ Тестовый PDF не найден: {test_pdf}")
        return False
    
    print(f"✅ Найден тестовый PDF: {test_pdf}")
    
    # Тестируем анализ документа
    print("\n🔍 Тестирование анализа документа...")
    try:
        analysis = smart_librarian.analyze_document(test_pdf)
        
        print(f"✅ Анализ завершен:")
        print(f"   📄 Файл: {analysis['file_name']}")
        print(f"   📊 Размер: {analysis['file_size'] / 1024:.1f} KB")
        print(f"   🏷️  Категория: {analysis['category']}")
        print(f"   🎯 Тип контента: {analysis['content_type']}")
        print(f"   🔑 Ключевые слова: {', '.join(analysis['keywords'][:5])}")
        print(f"   📈 Уверенность: {analysis['confidence']:.1%}")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False
    
    # Тестируем стратегию создания БЗ
    print("\n📚 Тестирование стратегии создания БЗ...")
    try:
        strategy = smart_librarian.suggest_kb_strategy([analysis])
        
        print(f"✅ Стратегия определена:")
        print(f"   🎯 Тип: {strategy['type']}")
        print(f"   📝 Обоснование: {strategy['reasoning']}")
        
        if strategy['type'] == 'single_kb':
            print(f"   📚 Название БЗ: {strategy['kb_name']}")
            print(f"   📄 Документов: {len(strategy['documents'])}")
        elif strategy['type'] == 'multiple_kb':
            print(f"   📚 Предложений БЗ: {len(strategy['kb_suggestions'])}")
        
    except Exception as e:
        print(f"❌ Ошибка стратегии: {e}")
        return False
    
    # Тестируем обработку документов
    print("\n🧠 Тестирование умной обработки документов...")
    try:
        result = smart_librarian.process_documents_smart([test_pdf])
        
        print(f"✅ Обработка завершена:")
        print(f"   📊 Анализов: {len(result['analyses'])}")
        print(f"   🎯 Стратегия: {result['strategy']['type']}")
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return False
    
    print("\n🎉 Все тесты исправления прошли успешно!")
    print("✅ Умный библиотекарь исправлен и готов к работе")
    
    return True

if __name__ == "__main__":
    success = test_smart_librarian_fix()
    if success:
        print("\n🚀 Умный библиотекарь готов к использованию!")
        print("📚 Откройте KB Admin: http://localhost:8502")
        print("🔍 Перейдите в раздел 'Умный библиотекарь'")
        print("📄 Попробуйте проанализировать billmaster_7.pdf")
    else:
        print("\n❌ Тесты не прошли")
        sys.exit(1)



