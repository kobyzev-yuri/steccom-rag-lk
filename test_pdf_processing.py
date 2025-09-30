#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки PDF в KB Admin
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.documents.pdf_processor import PDFProcessor
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager

def test_pdf_processing():
    """Тестирование обработки PDF"""
    print("🧪 Тестирование обработки PDF в KB Admin")
    print("=" * 50)
    
    # Инициализация
    pdf_processor = PDFProcessor("data/uploads")
    kb_manager = KnowledgeBaseManager()
    
    # Проверяем наличие тестового PDF
    test_pdf = Path("data/uploads/billmaster_7.pdf")
    if not test_pdf.exists():
        print(f"❌ Тестовый PDF не найден: {test_pdf}")
        return False
    
    print(f"✅ Найден тестовый PDF: {test_pdf}")
    
    # Тестируем извлечение текста
    print("\n📄 Тестирование извлечения текста...")
    try:
        text = pdf_processor.extract_text(str(test_pdf))
        if text and len(text.strip()) > 0:
            print(f"✅ Текст извлечен успешно ({len(text)} символов)")
            print(f"📝 Первые 200 символов: {text[:200]}...")
        else:
            print("❌ Текст не извлечен или пустой")
            return False
    except Exception as e:
        print(f"❌ Ошибка извлечения текста: {e}")
        return False
    
    # Тестируем получение метаданных
    print("\n📊 Тестирование получения метаданных...")
    try:
        metadata = pdf_processor.get_pdf_metadata(str(test_pdf))
        if metadata:
            print("✅ Метаданные получены:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        else:
            print("⚠️ Метаданные не получены")
    except Exception as e:
        print(f"❌ Ошибка получения метаданных: {e}")
    
    # Тестируем создание БЗ
    print("\n📚 Тестирование создания базы знаний...")
    try:
        kb_id = kb_manager.create_knowledge_base(
            name="Тестовая БЗ для billmaster_7",
            description="Тестовая база знаний для проверки обработки PDF",
            category="Тестирование",
            created_by="test_script"
        )
        print(f"✅ База знаний создана с ID: {kb_id}")
        
        # Тестируем добавление документа
        print("\n📄 Тестирование добавления документа...")
        with open(test_pdf, 'rb') as f:
            file_content = f.read()
        
        class MockUploadedFile:
            def __init__(self, name, content):
                self.name = name
                self._content = content
            
            def getvalue(self):
                return self._content
        
        mock_file = MockUploadedFile(test_pdf.name, file_content)
        
        result = pdf_processor.process_pdf(mock_file, kb_id, "billmaster_7")
        
        if result['success']:
            print("✅ PDF обработан успешно")
            
            # Добавляем документ в БЗ
            doc_id = kb_manager.add_document(
                kb_id,
                result['title'],
                result['file_path'],
                result['content_type'],
                result['file_size'],
                result['metadata']
            )
            print(f"✅ Документ добавлен в БЗ с ID: {doc_id}")
            
            # Обновляем статус
            kb_manager.update_document_status(doc_id, True, 'completed')
            print("✅ Статус документа обновлен")
            
        else:
            print(f"❌ Ошибка обработки PDF: {result.get('error', 'Неизвестная ошибка')}")
            return False
        
        # Проверяем результат
        docs = kb_manager.get_documents(kb_id)
        print(f"✅ В БЗ теперь {len(docs)} документов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания БЗ: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_processing()
    if success:
        print("\n🎉 Все тесты прошли успешно!")
        print("✅ KB Admin готов к работе с PDF документами")
    else:
        print("\n❌ Тесты не прошли")
        sys.exit(1)



