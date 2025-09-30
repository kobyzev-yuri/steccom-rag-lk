#!/usr/bin/env python3
"""
Тест интеграции Vision процессора с LLaVA-Phi3
"""

import sys
import os
sys.path.append('/mnt/ai/cnn/steccom')

from modules.documents.vision_processor import VisionProcessor
from modules.documents.ocr_processor import OCRProcessor

def test_vision_processor():
    """Тест Vision процессора"""
    print("🧪 Тестирование Vision процессора...")
    
    # Создаем процессор
    vision = VisionProcessor()
    
    # Проверяем доступность модели
    print("\n📋 Проверка доступности модели...")
    model_status = vision.check_model_availability()
    
    if model_status['available']:
        print(f"✅ Модель {model_status['model_name']} доступна")
        print(f"📊 Всего моделей: {len(model_status['all_models'])}")
    else:
        print(f"❌ Модель недоступна: {model_status.get('message', 'Unknown error')}")
        print(f"📊 Доступные модели: {model_status.get('all_models', [])}")
        return False
    
    # Получаем информацию о системе
    print("\n🔧 Информация о Vision системе:")
    vision_info = vision.get_vision_info()
    for key, value in vision_info.items():
        print(f"  {key}: {value}")
    
    return True

def test_ocr_processor():
    """Тест OCR процессора"""
    print("\n🧪 Тестирование OCR процессора...")
    
    # Создаем процессор
    ocr = OCRProcessor()
    
    # Получаем информацию об OCR
    print("\n🔧 Информация об OCR системе:")
    ocr_info = ocr.get_ocr_info()
    for key, value in ocr_info.items():
        print(f"  {key}: {value}")
    
    # Поддерживаемые форматы
    formats = ocr.get_supported_formats()
    print(f"\n📁 Поддерживаемые форматы: {', '.join(formats)}")
    
    return 'error' not in ocr_info

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование интеграции Vision и OCR процессоров")
    print("=" * 60)
    
    # Тест Vision
    vision_ok = test_vision_processor()
    
    # Тест OCR
    ocr_ok = test_ocr_processor()
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"👁️ Vision (LLaVA-Phi3): {'✅ Готов' if vision_ok else '❌ Не готов'}")
    print(f"🔍 OCR (Tesseract): {'✅ Готов' if ocr_ok else '❌ Не готов'}")
    
    if vision_ok and ocr_ok:
        print("\n🎉 Все системы готовы к работе!")
        print("\n💡 Рекомендации:")
        print("  - Vision лучше для анализа структуры документов")
        print("  - OCR лучше для точного извлечения текста")
        print("  - Автоматический режим выберет лучший результат")
    else:
        print("\n⚠️ Некоторые системы требуют настройки:")
        if not vision_ok:
            print("  - Установите LLaVA-Phi3: ollama pull llava-phi3:latest")
        if not ocr_ok:
            print("  - Установите Tesseract: sudo apt install tesseract-ocr tesseract-ocr-rus")

if __name__ == "__main__":
    main()


