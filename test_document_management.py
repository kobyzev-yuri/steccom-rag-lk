#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы управления документами
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "kb_admin"))

from kb_admin.modules.core.document_manager import DocumentManager

def test_document_management():
    """Тестирование системы управления документами"""
    print("📦 Тестирование системы управления документами")
    print("=" * 60)
    
    # Инициализация
    doc_manager = DocumentManager()
    
    # Проверяем наличие тестовых файлов
    upload_dir = Path("data/uploads")
    if not upload_dir.exists():
        print(f"❌ Директория uploads не найдена: {upload_dir}")
        return False
    
    pdf_files = list(upload_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Нет PDF файлов для тестирования")
        return False
    
    print(f"✅ Найдено {len(pdf_files)} PDF файлов для тестирования")
    
    # Тестируем сканирование директории
    print("\n🔍 Тестирование сканирования директории...")
    try:
        doc_status = doc_manager.scan_upload_directory()
        
        print(f"✅ Сканирование завершено:")
        print(f"   📄 Новые документы: {len(doc_status['new'])}")
        print(f"   ✅ Обработанные: {len(doc_status['processed'])}")
        print(f"   ❓ Неизвестные: {len(doc_status['unknown'])}")
        
        # Показываем детали
        if doc_status['new']:
            print("   🆕 Новые документы:")
            for doc in doc_status['new']:
                print(f"      • {doc['file_name']} ({doc['file_size']/1024:.1f} KB)")
        
        if doc_status['processed']:
            print("   ✅ Обработанные документы:")
            for doc in doc_status['processed']:
                print(f"      • {doc['file_name']} (БЗ ID: {doc.get('kb_info', {}).get('kb_id', 'N/A')})")
        
    except Exception as e:
        print(f"❌ Ошибка сканирования: {e}")
        return False
    
    # Тестируем получение информации об архиве
    print("\n📦 Тестирование информации об архиве...")
    try:
        archive_info = doc_manager.get_archive_info()
        
        print(f"✅ Информация об архиве:")
        print(f"   📦 Всего файлов: {archive_info['total_files']}")
        print(f"   💾 Общий размер: {archive_info['total_size']/1024/1024:.1f} MB")
        print(f"   📅 Дат в архиве: {len(archive_info['dates'])}")
        
        if archive_info['dates']:
            print("   📅 Архивы по датам:")
            for date_info in archive_info['dates'][:3]:  # Показываем первые 3
                print(f"      • {date_info['date']}: {date_info['files_count']} файлов ({date_info['size']/1024:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Ошибка получения информации об архиве: {e}")
        return False
    
    # Тестируем вычисление хеша файла
    print("\n🔐 Тестирование вычисления хеша...")
    try:
        test_file = pdf_files[0]
        file_hash = doc_manager.calculate_file_hash(test_file)
        
        print(f"✅ Хеш вычислен:")
        print(f"   📄 Файл: {test_file.name}")
        print(f"   🔐 Хеш: {file_hash[:16]}...")
        
    except Exception as e:
        print(f"❌ Ошибка вычисления хеша: {e}")
        return False
    
    # Тестируем регистрацию нового документа
    print("\n📝 Тестирование регистрации документа...")
    try:
        test_file = pdf_files[0]
        doc_manager.register_new_document(test_file)
        
        print(f"✅ Документ зарегистрирован: {test_file.name}")
        
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        return False
    
    print("\n🎉 Все тесты системы управления документами прошли успешно!")
    print("✅ Система готова к работе")
    
    return True

if __name__ == "__main__":
    success = test_document_management()
    if success:
        print("\n🚀 Система управления документами готова!")
        print("📚 Откройте KB Admin: http://localhost:8502")
        print("🔍 Перейдите в раздел 'Умный библиотекарь'")
        print("📦 Попробуйте режим 'Управление архивом'")
    else:
        print("\n❌ Тесты не прошли")
        sys.exit(1)



