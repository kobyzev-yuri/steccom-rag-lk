#!/usr/bin/env python3
"""
Скрипт для извлечения данных из billmaster_7.pdf и создания JSON
"""

import json
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('kb_admin/modules')

def extract_pdf_text(file_path):
    """Извлекаем текст из PDF"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Ошибка извлечения текста: {e}")
        return ""

def analyze_with_gemini(image_path):
    """Анализ изображения с помощью Gemini"""
    try:
        import requests
        import base64
        
        # Читаем изображение
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # API запрос к ProxyAPI для Gemini
        url = "https://api.proxyapi.ru/google/v1/models/gemini-2.0-flash:generateContent"
        headers = {
            "Authorization": "Bearer YOUR_API_KEY",  # Замените на ваш ключ
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Проанализируй это изображение и опиши его содержимое на русском языке. Если есть текст, извлеки его."
                }, {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        else:
            return f"Ошибка API: {response.status_code}"
            
    except Exception as e:
        return f"Ошибка анализа изображения: {e}"

def main():
    """Основная функция"""
    print("🔍 Извлекаем данные из billmaster_7.pdf...")
    
    # Пути к файлам
    pdf_path = Path("data/uploads/billmaster_7.pdf")
    image1_path = Path("data/extracted_images/billmaster_7_page_1_img_1.png")
    image2_path = Path("data/extracted_images/billmaster_7_page_2_img_1.png")
    
    # Проверяем существование файлов
    if not pdf_path.exists():
        print(f"❌ PDF файл не найден: {pdf_path}")
        return
    
    print(f"✅ PDF файл найден: {pdf_path}")
    
    # Извлекаем текст из PDF
    print("📄 Извлекаем текст из PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"✅ Извлечено {len(pdf_text)} символов текста")
    
    # Анализируем изображения
    images_data = []
    
    if image1_path.exists():
        print("🖼️ Анализируем изображение 1...")
        image1_analysis = analyze_with_gemini(image1_path)
        images_data.append({
            "image_name": "billmaster_7_page_1_img_1.png",
            "image_path": str(image1_path),
            "description": image1_analysis,
            "text_content": image1_analysis  # Для совместимости
        })
        print(f"✅ Анализ изображения 1 завершен")
    
    if image2_path.exists():
        print("🖼️ Анализируем изображение 2...")
        image2_analysis = analyze_with_gemini(image2_path)
        images_data.append({
            "image_name": "billmaster_7_page_2_img_1.png", 
            "image_path": str(image2_path),
            "description": image2_analysis,
            "text_content": image2_analysis  # Для совместимости
        })
        print(f"✅ Анализ изображения 2 завершен")
    
    # Создаем структуру данных
    analysis_data = {
        "file_name": "billmaster_7.pdf",
        "file_path": str(pdf_path),
        "content_type": "application/pdf",
        "file_size": pdf_path.stat().st_size,
        "category": "Лицензии и разрешения",
        "raw_ocr_text": pdf_text,
        "smart_summary": "Сертификат соответствия системы расчетов «Билл-Мастер» выдан органом сертификации Тест АХО «II KC» в Москве. Регистрационный номер сертификата: ОС-3-СТ-0274. Срок действия сертификата с 27 января 2010 года по 27 января 2011 года.",
        "original_cleaned_text": pdf_text,
        "images": images_data,
        "suggested_kb": {
            "suggested_name": "База знаний: Лицензии и разрешения",
            "suggested_category": "Лицензии и разрешения", 
            "description": "База знаний для документов категории Лицензии и разрешения",
            "can_merge_with": [],
            "merge_reason": "",
            "confidence": 0.9,
            "recommendations": ["Создать новую базу знаний"]
        }
    }
    
    # Сохраняем в JSON
    output_file = "billmaster_7_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON сохранен в {output_file}")
    print(f"📊 Статистика:")
    print(f"   - Текст: {len(pdf_text)} символов")
    print(f"   - Изображений: {len(images_data)}")
    print(f"   - Размер файла: {pdf_path.stat().st_size} байт")

if __name__ == "__main__":
    main()
