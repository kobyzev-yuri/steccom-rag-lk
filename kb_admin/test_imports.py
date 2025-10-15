#!/usr/bin/env python3
"""
Тест импортов для KB Admin
"""

from pdb import run
import sys
import os
from pathlib import Path

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules"))
sys.path.insert(0, str(current_dir.parent))
sys.path.insert(0, str(current_dir.parent.parent))

print("Python paths:")
for i, p in enumerate(sys.path[:10]):  # Показываем первые 10 путей
    print(f"{i}: {p}")

print("\nTesting imports...")

try:
    from modules.core.knowledge_manager import KnowledgeBaseManager
    print("✅ KnowledgeBaseManager imported")
except Exception as e:
    print(f"❌ KnowledgeBaseManager failed: {e}")
    # Попробуем прямой импорт
    try:
        import sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'modules', 'core'))
        from knowledge_manager import KnowledgeBaseManager
        print("✅ KnowledgeBaseManager imported (direct)")
    except Exception as e2:
        print(f"❌ KnowledgeBaseManager direct import failed: {e2}")
? Проанализируй
try:
    from modules.ui.main_interface import KBAdminInterface
    print("✅ KBAdminInterface imported")
except Exception as e:
    print(f"❌ KBAdminInterface failed: {e}")
    # Попробуем прямой импорт
    try:
        import sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'modules', 'ui'))
        from main_interface import KBAdminInterface
        print("✅ KBAdminInterface imported (direct)")
    except Exception as e2:
        print(f"❌ KBAdminInterface direct import failed: {e2}")

try:
    from modules.rag.multi_kb_rag import MultiKBRAG
    print("✅ MultiKBRAG imported")
except Exception as e:
    print(f"❌ MultiKBRAG failed: {e}")

print("\nTesting KBAdminInterface creation...")
try:
    interface = KBAdminInterface()
    print("✅ KBAdminInterface created successfully!")
    print(f"   RAG vectorstores: {len(interface.rag.vectorstores)}")
    print(f"   KB metadata: {len(interface.rag.kb_metadata)}")
except Exception as e:
    print(f"❌ KBAdminInterface creation failed: {e}")
    import traceback
    traceback.print_exc()
