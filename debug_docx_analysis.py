#!/usr/bin/env python3
"""
Отладка анализа DOCX файла
"""

import sys
import os
sys.path.append('/mnt/ai/cnn/steccom')

from kb_admin.modules.core.smart_document_agent import SmartLibrarian
from kb_admin.modules.core.knowledge_manager import KnowledgeBaseManager
from kb_admin.modules.documents.pdf_processor import PDFProcessor
from pathlib import Path

def debug_docx_analysis():
    """Отладка анализа DOCX файла"""
    print("🔍 Отладка анализа DOCX файла...")
    
    # Инициализируем компоненты
    kb_manager = KnowledgeBaseManager()
    pdf_processor = PDFProcessor()
    smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
    
    # Путь к файлу
    file_path = Path("/mnt/ai/cnn/steccom/data/uploads/Iridium Short Burst Data Service Best Practices Guide Draft 091410_1.docx")
    
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return
    
    print(f"📄 Анализируем файл: {file_path.name}")
    
    # Анализируем документ
    try:
        analysis = smart_librarian.analyze_document(file_path)
        
        if analysis is None:
            print("❌ Анализ вернул None")
            return
        
        print(f"✅ Анализ завершен, тип: {type(analysis)}")
        print(f"📊 Ключи в анализе: {list(analysis.keys()) if isinstance(analysis, dict) else 'Не словарь'}")
        
        if isinstance(analysis, dict):
            print(f"   - Формат: {analysis.get('format_description', 'Не указан')}")
            print(f"   - Поддерживается: {analysis.get('format_supported', 'Не указано')}")
            print(f"   - Длина текста: {analysis.get('text_length', 'Не указана')}")
            print(f"   - Категория: {analysis.get('category', 'Не указана')}")
            print(f"   - Тип контента: {analysis.get('content_type', 'Не указан')}")
            print(f"   - Есть умная выжимка: {'smart_summary' in analysis}")
            print(f"   - Есть предложение БЗ: {'suggested_kb' in analysis}")
        
        # Тестируем стратегию
        print("\n🎯 Тестируем стратегию создания БЗ...")
        strategy = smart_librarian.suggest_kb_strategy([analysis])
        
        print(f"✅ Стратегия создана, тип: {strategy.get('type', 'Не указан')}")
        print(f"📋 Ключи в стратегии: {list(strategy.keys())}")
        
        if strategy.get('type') == 'single_kb':
            print(f"   - Название БЗ: {strategy.get('kb_name', 'Не указано')}")
            print(f"   - Описание: {strategy.get('description', 'Не указано')}")
            print(f"   - Количество документов: {len(strategy.get('documents', []))}")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_docx_analysis()
