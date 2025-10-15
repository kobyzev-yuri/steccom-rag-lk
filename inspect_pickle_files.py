#!/usr/bin/env python3
"""
Inspect Pickle Files - Check what's inside the pickle files
Проверка Pickle файлов - посмотрим что внутри pickle файлов
"""

import pickle
from pathlib import Path

def inspect_pickle_files():
    """Проверяем содержимое pickle файлов"""
    
    vectorstore_paths = [
        "kb_admin/data/knowledge_bases/vectorstore_1",
        "kb_admin/data/knowledge_bases/vectorstore_2", 
        "kb_admin/data/knowledge_bases/vectorstore_3"
    ]
    
    for vectorstore_path in vectorstore_paths:
        pkl_file = Path(vectorstore_path) / "index.pkl"
        
        if pkl_file.exists():
            print(f"\n🔍 Проверка: {pkl_file}")
            
            try:
                with open(pkl_file, 'rb') as f:
                    data = pickle.load(f)
                
                print(f"   Тип объекта: {type(data)}")
                print(f"   Атрибуты: {dir(data)}")
                
                if hasattr(data, '__dict__'):
                    print(f"   Словарь атрибутов: {data.__dict__.keys()}")
                
                # Проверяем размер файла
                file_size = pkl_file.stat().st_size
                print(f"   Размер файла: {file_size} байт")
                
            except Exception as e:
                print(f"   ❌ Ошибка при загрузке: {e}")
        else:
            print(f"   ⚠️ Файл не найден: {pkl_file}")

if __name__ == "__main__":
    inspect_pickle_files()












