#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Умного библиотекаря
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
from kb_admin.modules.documents.pdf_processor import PDFProcessor

def test_smart_librarian():
    """Тестирование Умного библиотекаря"""
    print("📚 Тестирование Умного библиотекаря")
    print("=" * 50)
    
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
        
        if analysis['recommendations']:
            print(f"   💡 Рекомендации:")
            for rec in analysis['recommendations']:
                print(f"      • {rec}")
        
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
        
    except Exception as e:
        print(f"❌ Ошибка стратегии: {e}")
        return False
    
    print("\n🎉 Все тесты Умного библиотекаря прошли успешно!")
    print("✅ Умный библиотекарь готов к работе")
    
    return True

if __name__ == "__main__":
    success = test_smart_librarian()
    if success:
        print("\n🚀 Умный библиотекарь готов к использованию в KB Admin!")
        print("📚 Откройте KB Admin: http://localhost:8502")
        print("🔍 Перейдите в раздел 'Умный библиотекарь'")
    else:
        print("\n❌ Тесты не прошли")
        sys.exit(1)



