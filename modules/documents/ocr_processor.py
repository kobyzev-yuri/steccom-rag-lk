"""
OCR Document Processing Module
Обработка сканированных документов с помощью OCR
"""

import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path, convert_from_bytes
from typing import List, Dict, Optional, Union
import os
from pathlib import Path
import hashlib
import json
import tempfile
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, upload_dir: str = "data/uploads", tesseract_path: str = None):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка Tesseract (если указан путь)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Поддерживаемые форматы
        self.supported_formats = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Предобработка изображения для улучшения OCR"""
        try:
            # Конвертация в grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Увеличение контраста
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Удаление шума
            denoised = cv2.medianBlur(enhanced, 3)
            
            # Бинаризация (адаптивная)
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Морфологические операции для очистки
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Ошибка предобработки изображения: {e}")
            return image
    
    def extract_text_from_image(self, image: Union[str, np.ndarray, Image.Image], 
                              preprocess: bool = True) -> str:
        """Извлечение текста из изображения с помощью OCR"""
        try:
            # Конвертация в PIL Image если нужно
            if isinstance(image, str):
                pil_image = Image.open(image)
            elif isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # Предобработка если включена
            if preprocess:
                # Конвертация PIL в numpy для OpenCV
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                processed_image = self.preprocess_image(cv_image)
                # Обратно в PIL
                pil_image = Image.fromarray(processed_image)
            
            # OCR с настройками для русского языка
            custom_config = r'--oem 3 --psm 6 -l rus+eng'
            text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return ""
    
    def extract_text_from_pdf_scans(self, pdf_path: str, dpi: int = 300) -> str:
        """Извлечение текста из PDF-сканов"""
        try:
            # Конвертация PDF в изображения
            images = convert_from_path(pdf_path, dpi=dpi)
            
            all_text = []
            for i, image in enumerate(images):
                logger.info(f"Обработка страницы {i+1}/{len(images)}")
                
                # OCR для каждой страницы
                page_text = self.extract_text_from_image(image, preprocess=True)
                if page_text:
                    all_text.append(f"--- Страница {i+1} ---\n{page_text}\n")
            
            return "\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Ошибка обработки PDF-сканов: {e}")
            return ""
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes, dpi: int = 300) -> str:
        """Извлечение текста из PDF-сканов (из байтов)"""
        try:
            # Конвертация PDF в изображения
            images = convert_from_bytes(pdf_bytes, dpi=dpi)
            
            all_text = []
            for i, image in enumerate(images):
                logger.info(f"Обработка страницы {i+1}/{len(images)}")
                
                # OCR для каждой страницы
                page_text = self.extract_text_from_image(image, preprocess=True)
                if page_text:
                    all_text.append(f"--- Страница {i+1} ---\n{page_text}\n")
            
            return "\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Ошибка обработки PDF-сканов из байтов: {e}")
            return ""
    
    def is_scanned_pdf(self, pdf_path: str, threshold: int = 50) -> bool:
        """Определение, является ли PDF сканированным документом"""
        try:
            # Пробуем извлечь текст обычными методами
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages[:3]:  # Проверяем первые 3 страницы
                    text += page.extract_text()
            
            # Если текста мало, скорее всего это сканы
            return len(text.strip()) < threshold
            
        except Exception:
            return True  # Если не можем прочитать, считаем сканом
    
    def process_document(self, file_path: str, file_type: str = None) -> Dict:
        """Универсальная обработка документа (текст + OCR)"""
        try:
            file_path = Path(file_path)
            file_type = file_type or file_path.suffix.lower()
            
            result = {
                'success': False,
                'text_content': '',
                'extraction_method': 'unknown',
                'metadata': {
                    'original_file': str(file_path),
                    'file_type': file_type,
                    'file_size': file_path.stat().st_size
                }
            }
            
            if file_type == '.pdf':
                # Сначала пробуем обычное извлечение текста
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    
                    # Если текста достаточно, используем его
                    if len(text.strip()) > 100:
                        result['text_content'] = text.strip()
                        result['extraction_method'] = 'pypdf2'
                        result['success'] = True
                        return result
                    
                except Exception as e:
                    logger.warning(f"PyPDF2 не сработал: {e}")
                
                # Если текста мало, пробуем OCR
                logger.info("Пробуем OCR для PDF...")
                ocr_text = self.extract_text_from_pdf_scans(str(file_path))
                if ocr_text:
                    result['text_content'] = ocr_text
                    result['extraction_method'] = 'ocr_pdf'
                    result['success'] = True
                else:
                    result['error'] = "Не удалось извлечь текст ни одним методом"
            
            elif file_type in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}:
                # Обработка изображений
                logger.info(f"OCR для изображения: {file_path}")
                ocr_text = self.extract_text_from_image(str(file_path))
                if ocr_text:
                    result['text_content'] = ocr_text
                    result['extraction_method'] = 'ocr_image'
                    result['success'] = True
                else:
                    result['error'] = "Не удалось извлечь текст из изображения"
            
            else:
                result['error'] = f"Неподдерживаемый формат: {file_type}"
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text_content': '',
                'extraction_method': 'error'
            }
    
    def process_uploaded_file(self, uploaded_file, kb_id: int, title: str = None) -> Dict:
        """Обработка загруженного файла с OCR"""
        try:
            # Генерируем имя файла
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
            file_extension = Path(uploaded_file.name).suffix
            filename = f"{file_hash}{file_extension}"
            file_path = self.upload_dir / filename
            
            # Сохраняем файл
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Обрабатываем документ
            result = self.process_document(str(file_path))
            
            if result['success']:
                # Добавляем метаданные
                result['metadata'].update({
                    'original_filename': uploaded_file.name,
                    'file_hash': file_hash,
                    'kb_id': kb_id,
                    'file_path': str(file_path)
                })
                
                result['title'] = title or uploaded_file.name
                result['file_path'] = str(file_path)
                result['file_size'] = file_path.stat().st_size
                
                # Определяем content_type
                if file_extension == '.pdf':
                    result['content_type'] = 'application/pdf'
                elif file_extension in {'.png', '.jpg', '.jpeg'}:
                    result['content_type'] = f'image/{file_extension[1:]}'
                else:
                    result['content_type'] = 'application/octet-stream'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text_content': '',
                'extraction_method': 'error'
            }
    
    def get_supported_formats(self) -> List[str]:
        """Получить список поддерживаемых форматов"""
        return list(self.supported_formats)
    
    def get_ocr_info(self) -> Dict:
        """Получить информацию о настройках OCR"""
        try:
            version = pytesseract.get_tesseract_version()
            languages = pytesseract.get_languages()
            return {
                'tesseract_version': version,
                'available_languages': languages,
                'tesseract_path': pytesseract.pytesseract.tesseract_cmd
            }
        except Exception as e:
            return {
                'error': str(e),
                'tesseract_available': False
            }

