#!/usr/bin/env python3
"""
Тестирование OCR отдельно
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path
import os

def test_ocr_on_pdf():
    """Тестирование OCR на billmaster_7.pdf"""
    
    pdf_path = "/mnt/ai/cnn/steccom/data/uploads/billmaster_7.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Файл не найден: {pdf_path}")
        return
    
    print(f"🔍 Тестируем OCR на файле: {pdf_path}")
    
    try:
        # Конвертируем PDF в изображения
        print("📄 Конвертируем PDF в изображения...")
        images = convert_from_path(pdf_path, dpi=300)
        print(f"✅ Получено {len(images)} страниц")
        
        # Тестируем разные настройки OCR
        configs = [
            ("Базовый русский", r'--oem 3 --psm 6 -l rus'),
            ("Русский + английский", r'--oem 3 --psm 6 -l rus+eng'),
            ("Автоматическая сегментация", r'--oem 3 --psm 3 -l rus+eng'),
            ("С OSD", r'--oem 3 --psm 1 -l rus+eng'),
            ("Один столбец", r'--oem 3 --psm 4 -l rus+eng'),
            ("Только русский PSM 6", r'--oem 3 --psm 6 -l rus'),
            ("Только русский PSM 3", r'--oem 3 --psm 3 -l rus'),
        ]
        
        for page_num, image in enumerate(images[:1]):  # Тестируем только первую страницу
            print(f"\n📖 Страница {page_num + 1}:")
            
            for config_name, config in configs:
                try:
                    print(f"\n🔧 {config_name}:")
                    print(f"   Конфиг: {config}")
                    
                    text = pytesseract.image_to_string(image, config=config)
                    text_preview = text[:200].replace('\n', ' ').strip()
                    
                    print(f"   Результат ({len(text)} символов): {text_preview}...")
                    
                    if len(text.strip()) > 50:
                        print(f"   ✅ Хороший результат!")
                    else:
                        print(f"   ⚠️ Мало текста")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка: {e}")
        
        # Тестируем с предобработкой
        print(f"\n🖼️ Тестируем с предобработкой изображения:")
        
        # Конвертируем PIL в OpenCV
        cv_image = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
        
        # Предобработка
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Увеличение размера
        scale_factor = 2.0
        new_width = int(gray.shape[1] * scale_factor)
        new_height = int(gray.shape[0] * scale_factor)
        resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Увеличение контраста
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Удаление шума
        denoised = cv2.medianBlur(enhanced, 3)
        
        # Бинаризация
        binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Обратно в PIL
        processed_image = Image.fromarray(binary)
        
        # OCR с предобработкой
        config = r'--oem 3 --psm 6 -l rus+eng'
        text = pytesseract.image_to_string(processed_image, config=config)
        text_preview = text[:200].replace('\n', ' ').strip()
        
        print(f"   Результат с предобработкой ({len(text)} символов): {text_preview}...")
        
        if len(text.strip()) > 50:
            print(f"   ✅ Хороший результат с предобработкой!")
        else:
            print(f"   ⚠️ Мало текста даже с предобработкой")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_tesseract_langs():
    """Проверяем доступные языки"""
    print("🌐 Проверяем доступные языки Tesseract:")
    try:
        langs = pytesseract.get_languages()
        print(f"   Доступные языки: {langs}")
        
        if 'rus' in langs:
            print("   ✅ Русский язык доступен")
        else:
            print("   ❌ Русский язык НЕ доступен")
            
    except Exception as e:
        print(f"   ❌ Ошибка получения языков: {e}")

if __name__ == "__main__":
    print("🚀 Тестирование OCR")
    print("=" * 50)
    
    test_tesseract_langs()
    print()
    test_ocr_on_pdf()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")

