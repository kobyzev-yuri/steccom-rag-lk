#!/usr/bin/env python3
"""
Скрипт для пересоздания векторных индексов с оптимальными настройками
для коротких независимых абзацев в регламентах
"""

import os
import sys
import json
import sqlite3
import shutil
from pathlib import Path
from typing import List, Dict
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.rag.multi_kb_rag import MultiKBRAG
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


def analyze_text_structure(text: str) -> Dict:
    """Анализ структуры текста для определения оптимальных настроек"""
    analysis = {
        'total_length': len(text),
        'paragraphs_by_double_newline': len([p for p in text.split('\n\n') if p.strip()]),
        'lines_by_single_newline': len([l for l in text.split('\n') if l.strip()]),
        'sections_by_numbers': len(re.split(r'\n\s*(\d+\.\s)', text)),
        'avg_section_length': 0,
        'section_lengths': []
    }
    
    # Анализируем разделы по номерам
    sections = re.split(r'\n\s*(\d+\.\s)', text)
    section_lengths = []
    
    # Берем содержимое разделов (каждый второй элемент после разделителя)
    for i in range(1, len(sections), 2):
        if i < len(sections):
            section_content = sections[i]
            if section_content.strip():
                section_lengths.append(len(section_content.strip()))
    
    # Если разделы не найдены, анализируем по абзацам
    if not section_lengths:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        section_lengths = [len(p) for p in paragraphs if len(p) > 50]  # Игнорируем очень короткие абзацы
    
    analysis['section_lengths'] = section_lengths
    analysis['avg_section_length'] = sum(section_lengths) / len(section_lengths) if section_lengths else 0
    
    return analysis


def create_optimal_text_splitter(text_analysis: Dict) -> RecursiveCharacterTextSplitter:
    """Создание оптимального text splitter на основе анализа текста"""
    
    # Определяем оптимальный размер чанка
    avg_section_length = text_analysis['avg_section_length']
    
    if avg_section_length < 500:
        chunk_size = 500
        chunk_overlap = 50
    elif avg_section_length < 1000:
        chunk_size = 800
        chunk_overlap = 100
    else:
        chunk_size = 1200
        chunk_overlap = 150
    
    print(f"📊 Анализ текста:")
    print(f"   Средняя длина раздела: {avg_section_length:.0f} символов")
    print(f"   Выбранный размер чанка: {chunk_size}")
    print(f"   Перекрытие: {chunk_overlap}")
    
    # Оптимизированные разделители для регламентов
    separators = [
        "\n\n",  # Двойные переносы строк (абзацы)
        "\n",    # Одинарные переносы строк
        ". ",    # Точки с пробелом
        "! ",    # Восклицательные знаки
        "? ",    # Вопросительные знаки
        "; ",    # Точки с запятой
        ", ",    # Запятые
        " ",     # Пробелы
        ""       # Последний резорт
    ]
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=separators
    )


def recreate_kb_indexes(kb_ids: List[int] = None):
    """Пересоздание векторных индексов для указанных KB"""
    
    print("🚀 Пересоздание векторных индексов Knowledge Base")
    print("=" * 60)
    
    # Инициализируем RAG систему
    rag = MultiKBRAG()
    
    # Если не указаны KB, берем все активные
    if kb_ids is None:
        available_kbs = rag.get_available_kbs()
        kb_ids = [kb.get('id', i) for i, kb in enumerate(available_kbs, 1)]
    
    print(f"📚 Будет пересоздано индексов: {len(kb_ids)}")
    
    for kb_id in kb_ids:
        print(f"\n🔄 Обрабатываем KB ID: {kb_id}")
        
        try:
            # Удаляем старый векторный индекс
            vectorstore_path = f"data/knowledge_bases/vectorstore_{kb_id}"
            if Path(vectorstore_path).exists():
                shutil.rmtree(vectorstore_path)
                print(f"   🗑️  Удален старый индекс: {vectorstore_path}")
            
            # Получаем информацию о KB из базы данных
            conn = sqlite3.connect(rag.db_path)
            c = conn.cursor()
            
            c.execute("SELECT * FROM knowledge_bases WHERE id = ? AND is_active = 1", (kb_id,))
            kb_info = c.fetchone()
            
            if not kb_info:
                print(f"   ❌ KB {kb_id} не найдена или неактивна")
                conn.close()
                continue
            
            print(f"   📖 KB: {kb_info[1]} ({kb_info[3]})")
            
            # Получаем документы для этой KB
            c.execute("SELECT * FROM knowledge_documents WHERE kb_id = ?", (kb_id,))
            documents = c.fetchall()
            
            if not documents:
                print(f"   ⚠️  Нет документов в KB {kb_id}")
                conn.close()
                continue
            
            print(f"   📄 Документов: {len(documents)}")
            
            # Анализируем структуру текста для определения оптимальных настроек
            all_text = ""
            for doc in documents:
                # Контент может быть в metadata или в file_path
                if doc[9]:  # metadata
                    try:
                        metadata = json.loads(doc[9])
                        if 'content' in metadata:
                            all_text += metadata['content'] + "\n\n"
                    except:
                        pass
                elif doc[3]:  # file_path - читаем файл
                    try:
                        with open(doc[3], 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            all_text += file_content + "\n\n"
                    except:
                        pass
            
            if all_text.strip():
                text_analysis = analyze_text_structure(all_text)
                text_splitter = create_optimal_text_splitter(text_analysis)
            else:
                # Используем настройки по умолчанию
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=600,  # Уменьшенный размер для коротких абзацев
                    chunk_overlap=100,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
                )
                print(f"   📊 Используются настройки по умолчанию: chunk_size=600, overlap=100")
            
            # Создаем документы для обработки
            documents_list = []
            for doc in documents:
                content = ""
                
                # Получаем контент из metadata или файла
                if doc[9]:  # metadata
                    try:
                        metadata = json.loads(doc[9])
                        if 'content' in metadata:
                            content = metadata['content']
                    except:
                        pass
                
                if not content and doc[3]:  # file_path - читаем файл
                    try:
                        with open(doc[3], 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        pass
                
                if content:
                    doc_metadata = {
                        'kb_id': kb_id,
                        'doc_id': doc[0],
                        'title': doc[1] or 'Без названия',
                        'source': 'db',
                        'category': kb_info[3]
                    }
                    
                    documents_list.append(Document(
                        page_content=content,
                        metadata=doc_metadata
                    ))
            
            if not documents_list:
                print(f"   ❌ Нет контента для обработки в KB {kb_id}")
                conn.close()
                continue
            
            # Разбиваем документы на чанки
            print(f"   ✂️  Разбиваем на чанки...")
            chunks = text_splitter.split_documents(documents_list)
            print(f"   📦 Создано чанков: {len(chunks)}")
            
            # Показываем примеры чанков
            for i, chunk in enumerate(chunks[:3]):
                print(f"      Чанк {i+1}: {len(chunk.page_content)} символов - {chunk.page_content[:100]}...")
            
            # Создаем новый векторный индекс
            print(f"   🔍 Создаем векторный индекс...")
            from langchain_community.vectorstores import FAISS
            vectorstore = FAISS.from_documents(chunks, rag.embeddings)
            
            # Сохраняем индекс на диск
            vectorstore.save_local(vectorstore_path)
            print(f"   💾 Сохранен новый индекс: {vectorstore_path}")
            
            # Обновляем метаданные в памяти
            rag.vectorstores[kb_id] = vectorstore
            rag.kb_metadata[kb_id] = {
                'name': kb_info[1],
                'description': kb_info[2],
                'category': kb_info[3],
                'doc_count': len(documents),
                'chunk_count': len(chunks)
            }
            
            print(f"   ✅ KB {kb_id} успешно пересоздана")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Ошибка при обработке KB {kb_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Пересоздание индексов завершено!")
    print(f"📊 Статистика:")
    for kb_id in kb_ids:
        if kb_id in rag.kb_metadata:
            metadata = rag.kb_metadata[kb_id]
            print(f"   • KB {kb_id} ({metadata['name']}): {metadata['chunk_count']} чанков")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Пересоздание векторных индексов KB')
    parser.add_argument('--kb-ids', nargs='+', type=int, help='ID KB для пересоздания (по умолчанию все)')
    parser.add_argument('--analyze-only', action='store_true', help='Только анализ структуры текста')
    
    args = parser.parse_args()
    
    if args.analyze_only:
        # Только анализ структуры
        print("📊 Анализ структуры текста в KB...")
        
        rag = MultiKBRAG()
        available_kbs = rag.get_available_kbs()
        
        for kb in available_kbs:
            kb_id = kb.get('id', 1)
            print(f"\n📖 KB: {kb['name']} (ID: {kb_id})")
            
            # Получаем документы
            conn = sqlite3.connect(rag.db_path)
            c = conn.cursor()
            c.execute("SELECT metadata, file_path FROM knowledge_documents WHERE kb_id = ?", (kb_id,))
            documents = c.fetchall()
            conn.close()
            
            all_text = ""
            for doc in documents:
                content = ""
                if doc[0]:  # metadata
                    try:
                        metadata = json.loads(doc[0])
                        if 'content' in metadata:
                            content = metadata['content']
                    except:
                        pass
                
                if not content and doc[1]:  # file_path
                    try:
                        with open(doc[1], 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        pass
                
                if content:
                    all_text += content + "\n\n"
            if all_text:
                analysis = analyze_text_structure(all_text)
                print(f"   Общая длина: {analysis['total_length']} символов")
                print(f"   Разделов: {analysis['sections_by_numbers']}")
                print(f"   Средняя длина раздела: {analysis['avg_section_length']:.0f} символов")
                print(f"   Рекомендуемый размер чанка: {min(800, max(400, int(analysis['avg_section_length'] * 0.8)))}")
    else:
        # Пересоздание индексов
        recreate_kb_indexes(args.kb_ids)


if __name__ == "__main__":
    main()
