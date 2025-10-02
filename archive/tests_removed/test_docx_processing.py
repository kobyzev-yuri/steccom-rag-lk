#!/usr/bin/env python3
"""
Тест обработки DOCX документов в KB Admin
"""

import sys
from pathlib import Path

# Добавляем путь к модулям KB Admin
sys.path.insert(0, str(Path(__file__).parent / "kb_admin"))

from modules.core.smart_document_agent import SmartLibrarian
from modules.core.knowledge_manager import KnowledgeBaseManager
from modules.documents.pdf_processor import PDFProcessor

def test_docx_processing():
    """Тест обработки DOCX файла"""
    print("🧪 Тестирование обработки DOCX документов...")
    
    # Инициализируем компоненты
    kb_manager = KnowledgeBaseManager()
    pdf_processor = PDFProcessor()
    smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
    
    # Путь к DOCX файлу (берем один из доступных образцов)
    candidates = [
        Path("data/uploads/Договор на услуги М2М Иридиум (юр.лица)-2020-3.docx"),
        Path("data/uploads/Iridium Short Burst Data Service Best Practices Guide Draft 091410_1.docx"),
        Path("data/uploads/LinuxFAQ.docx"),
    ]
    docx_file = next((p for p in candidates if p.exists()), candidates[0])
    
    if not docx_file.exists():
        print(f"❌ Файл не найден: {docx_file}")
        return False
    
    print(f"📄 Обрабатываем файл: {docx_file.name}")
    
    try:
        # Анализируем документ
        analysis = smart_librarian.analyze_document(docx_file)
        
        print(f"✅ Анализ завершен:")
        print(f"   - Формат: {analysis.get('format_description', 'Неизвестно')}")
        print(f"   - Поддерживается: {analysis.get('format_supported', False)}")
        print(f"   - Длина текста: {analysis.get('text_length', 0)} символов")
        print(f"   - Тип контента: {analysis.get('content_type', 'Неизвестно')}")
        print(f"   - Категория: {analysis.get('suggested_category', 'Неизвестно')}")
        
        # Показываем превью текста
        text_preview = analysis.get('text_preview', '')
        if text_preview:
            print(f"📝 Превью текста (первые 200 символов):")
            print(f"   {text_preview[:200]}...")
        
        # Показываем умную выжимку
        smart_summary = analysis.get('smart_summary', '')
        if smart_summary:
            print(f"🧠 Умная выжимка:")
            print(f"   {smart_summary[:300]}...")
        
        # Показываем рекомендации по KB
        kb_suggestion = analysis.get('suggested_kb', {})
        if kb_suggestion:
            print(f"💡 Рекомендация по KB:")
            print(f"   - Название: {kb_suggestion.get('suggested_name', 'Неизвестно')}")
            print(f"   - Категория: {kb_suggestion.get('suggested_category', 'Неизвестно')}")
            print(f"   - Описание: {kb_suggestion.get('description', 'Неизвестно')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обработке DOCX: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_docx_processing()
    if success:
        print("\n🎉 Тест обработки DOCX прошел успешно!")
    else:
        print("\n💥 Тест обработки DOCX завершился с ошибкой!")
        sys.exit(1)
