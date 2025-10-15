#!/usr/bin/env python3
"""
Inspect Tuple Content - Check what's inside the tuple pickle files
Проверка содержимого Tuple - посмотрим что внутри tuple pickle файлов
"""

import pickle
from pathlib import Path

def inspect_tuple_content():
    """Проверяем содержимое tuple в pickle файлах"""
    
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
                
                print(f"   Тип: {type(data)}")
                print(f"   Длина tuple: {len(data)}")
                
                for i, item in enumerate(data):
                    print(f"   Элемент {i}: {type(item)}")
                    if hasattr(item, '__dict__'):
                        print(f"     Атрибуты: {list(item.__dict__.keys())}")
                    elif hasattr(item, 'shape'):
                        print(f"     Форма: {item.shape}")
                    else:
                        print(f"     Значение: {str(item)[:100]}...")
                
            except Exception as e:
                print(f"   ❌ Ошибка при загрузке: {e}")

if __name__ == "__main__":
    inspect_tuple_content()












