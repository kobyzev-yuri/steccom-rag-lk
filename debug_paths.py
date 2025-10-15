#!/usr/bin/env python3
"""
Debug Paths - Check what paths are being used
Проверка путей в RAG системе
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def debug_paths():
    """Проверяем пути"""
    
    print("🔍 Отладка путей:")
    
    # Текущая рабочая директория
    print(f"📁 Текущая рабочая директория: {Path.cwd()}")
    
    # Путь к файлу multi_kb_rag.py
    rag_file = Path(__file__).parent / "kb_admin" / "modules" / "rag" / "multi_kb_rag.py"
    print(f"📄 Путь к multi_kb_rag.py: {rag_file}")
    print(f"📄 Существует ли файл: {rag_file.exists()}")
    
    # Путь как в коде
    current_dir = rag_file.parent.parent.parent
    print(f"📁 current_dir (parent.parent.parent): {current_dir}")
    
    # Путь к векторным индексам
    vectorstore_path = current_dir / "data" / "knowledge_bases" / "vectorstore_1"
    print(f"📁 Путь к vectorstore_1: {vectorstore_path}")
    print(f"📁 Существует ли папка: {vectorstore_path.exists()}")
    
    if vectorstore_path.exists():
        print(f"📄 Содержимое папки:")
        for item in vectorstore_path.iterdir():
            print(f"   - {item.name}")
    
    # Абсолютный путь
    abs_vectorstore_path = vectorstore_path.resolve()
    print(f"📁 Абсолютный путь: {abs_vectorstore_path}")
    
    # Проверим файлы index.faiss
    faiss_file = vectorstore_path / "index.faiss"
    print(f"📄 index.faiss существует: {faiss_file.exists()}")
    
    pkl_file = vectorstore_path / "index.pkl"
    print(f"📄 index.pkl существует: {pkl_file.exists()}")

if __name__ == "__main__":
    debug_paths()












