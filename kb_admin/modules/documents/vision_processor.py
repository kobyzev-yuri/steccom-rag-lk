"""
Vision Processor для KB Admin
Упрощенная версия для работы с изображениями через Gemini
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Упрощенный процессор изображений для KB Admin"""
    
    def __init__(self):
        # Настройки для Gemini через ProxyAPI
        import os
        self.use_gemini = os.getenv("USE_GEMINI", "true").lower() == "true"
        self.proxy_api_key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
        
        # Используем конфигурацию по умолчанию
        try:
            from config.settings import MODEL_DEFAULTS
            self.gemini_model = os.getenv("STEC_VISION_MODEL", MODEL_DEFAULTS.get("VISION_MODEL", "gemini-2.0-flash"))
        except ImportError:
            self.gemini_model = os.getenv("STEC_VISION_MODEL", "gemini-2.0-flash")
    
    def check_model_availability(self) -> Dict[str, Any]:
        """Проверить доступность модели"""
        try:
            # Проверяем Gemini через ProxyAPI
            if self.use_gemini and self.proxy_api_key:
                try:
                    import requests
                    headers = {
                        "Authorization": f"Bearer {self.proxy_api_key}",
                        "Content-Type": "application/json"
                    }
                    # Проверяем доступность Google Gemini через ProxyAPI
                    response = requests.get(
                        "https://api.proxyapi.ru/google/v1/models",
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code == 200:
                        return {'available': True, 'message': f'Google Gemini {self.gemini_model} доступен через ProxyAPI'}
                    else:
                        return {'available': False, 'message': f'ProxyAPI недоступен: {response.status_code}'}
                except Exception as e:
                    return {'available': False, 'message': f'Ошибка проверки ProxyAPI: {e}'}
            
            # Если Gemini не настроен, возвращаем ошибку
            return {'available': False, 'message': 'Google Gemini не настроен - требуется PROXYAPI_KEY'}
        except Exception as e:
            return {'available': False, 'message': f'Ошибка проверки модели: {e}'}
    
    def analyze_image_with_gemini(self, image_path: Path) -> Dict[str, Any]:
        """Анализ изображения с помощью Google Gemini (оптимизировано для больших изображений)"""
        try:
            import requests
            import base64
            from PIL import Image
            import io
            
            # Проверяем размер изображения
            file_size = image_path.stat().st_size
            if file_size > 20 * 1024 * 1024:  # Увеличили лимит до 20MB для больших PDF изображений
                return {
                    'success': False,
                    'error': f'Изображение слишком большое: {file_size / 1024 / 1024:.1f}MB'
                }
            
            # Оптимизируем изображение для больших PDF сканов
            try:
                image = Image.open(image_path)
                
                # Для больших изображений используем более умное масштабирование
                max_size = 2048 if file_size > 5 * 1024 * 1024 else 1024  # Больше размер для больших файлов
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Конвертируем в RGB если нужно
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Сохраняем в буфер с оптимальным качеством
                img_buffer = io.BytesIO()
                quality = 90 if file_size > 2 * 1024 * 1024 else 85  # Выше качество для больших файлов
                image.save(img_buffer, format='JPEG', quality=quality)
                img_data = img_buffer.getvalue()
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Ошибка обработки изображения: {e}'
                }
            
            # Кодируем в base64
            image_data = base64.b64encode(img_data).decode()
            
            # Используем Google Gemini через ProxyAPI
            if self.use_gemini and self.proxy_api_key:
                return self._analyze_with_gemini(image_data, image_path.name)
            else:
                # Если Gemini не настроен, возвращаем ошибку
                return {
                    'success': False,
                    'error': 'Google Gemini не настроен - требуется PROXYAPI_KEY',
                    'provider': 'gemini'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка анализа изображения: {e}'
            }
    
    def _analyze_with_gemini(self, image_data: str, image_name: str) -> Dict[str, Any]:
        """Анализ изображения с помощью Google Gemini через ProxyAPI"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.proxy_api_key}",
            "Content-Type": "application/json"
        }
        
        # Используем Google Gemini API формат с улучшенным промптом для больших изображений
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"""Проанализируй это изображение документа '{image_name}' детально. 

Для больших изображений и PDF сканов:
1. Опиши общую структуру и компоновку
2. Извлеки весь видимый текст (сохрани форматирование)
3. Определи тип документа (технический, юридический, инструкция и т.д.)
4. Выдели ключевые разделы, заголовки, таблицы
5. Опиши схемы, диаграммы, графики если есть
6. Укажи важные технические характеристики или данные

Ответь подробно на русском языке, сохраняя структуру документа."""
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1500  # Увеличили лимит для больших изображений
            }
        }
        
        response = requests.post(
            f"https://api.proxyapi.ru/google/v1/models/{self.gemini_model}:generateContent",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                analysis_text = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'model': self.gemini_model,
                    'provider': 'gemini'
                }
            else:
                raise Exception(f'Неожиданный формат ответа Gemini: {result}')
        else:
            raise Exception(f'Gemini API error: {response.status_code} - {response.text}')
    
    def extract_text_from_image_gemini(self, image_path: Path) -> str:
        """Извлечение текста из изображения с помощью Gemini (оптимизировано для больших изображений)"""
        try:
            import requests
            import base64
            from PIL import Image
            import io
            
            # Проверяем размер изображения
            file_size = image_path.stat().st_size
            if file_size > 20 * 1024 * 1024:  # Увеличили лимит до 20MB
                return f'Изображение слишком большое: {file_size / 1024 / 1024:.1f}MB'
            
            # Оптимизируем изображение для больших PDF сканов
            try:
                image = Image.open(image_path)
                
                # Для больших изображений используем более умное масштабирование
                max_size = 2048 if file_size > 5 * 1024 * 1024 else 1024
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Конвертируем в RGB если нужно
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Сохраняем в буфер с оптимальным качеством
                img_buffer = io.BytesIO()
                quality = 90 if file_size > 2 * 1024 * 1024 else 85
                image.save(img_buffer, format='JPEG', quality=quality)
                img_data = img_buffer.getvalue()
            except Exception as e:
                return f'Ошибка обработки изображения: {e}'
            
            # Кодируем в base64
            image_data = base64.b64encode(img_data).decode()
            
            # Используем Gemini для извлечения текста
            if self.use_gemini and self.proxy_api_key:
                try:
                    text = self._extract_text_with_gemini(image_data)
                    # Применяем очистку OCR текста
                    cleaned_text = self._clean_ocr_text(text)
                    return cleaned_text
                except Exception as gemini_error:
                    logger.warning(f"Gemini недоступен для извлечения текста: {gemini_error}")
                    return "Ошибка извлечения текста через Gemini"
            else:
                return "Gemini не настроен для извлечения текста"
                
        except Exception as e:
            return f'Ошибка извлечения текста: {e}'
    
    def _extract_text_with_gemini(self, image_data: str) -> str:
        """Извлечение текста с помощью Google Gemini"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.proxy_api_key}",
            "Content-Type": "application/json"
        }
        
        # Используем Google Gemini API формат с улучшенным промптом для больших изображений
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": """Извлеки весь текст с этого изображения максимально точно. 

Для больших изображений и PDF сканов:
1. Сохрани структуру документа (заголовки, абзацы, списки)
2. Извлеки текст из таблиц, сохраняя форматирование
3. Обрати внимание на мелкий текст и подписи
4. Если есть схемы или диаграммы, опиши их содержимое
5. Сохрани нумерацию и маркировку
6. Если текст неразборчив, укажи это, но попробуй расшифровать

Выдай результат в том же порядке, что и в документе."""
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2000  # Увеличили лимит для больших изображений
            }
        }
        
        response = requests.post(
            f"https://api.proxyapi.ru/google/v1/models/{self.gemini_model}:generateContent",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception(f'Неожиданный формат ответа Gemini: {result}')
        else:
            raise Exception(f'Gemini API error: {response.status_code} - {response.text}')
    
    def _clean_ocr_text(self, text: str) -> str:
        """Базовая очистка OCR текста"""
        if not text:
            return ""
        
        # Убираем лишние пробелы и переносы
        text = ' '.join(text.split())
        
        # Убираем специальные символы OCR
        import re
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'№]', ' ', text)
        
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze_document_structure(self, image_path: Path) -> Dict[str, Any]:
        """Анализ структуры документа"""
        try:
            import requests
            import base64
            from PIL import Image
            import io
            
            # Проверяем размер изображения
            file_size = image_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                return {
                    'success': False,
                    'error': f'Изображение слишком большое: {file_size / 1024 / 1024:.1f}MB'
                }
            
            # Уменьшаем размер изображения
            try:
                image = Image.open(image_path)
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='JPEG', quality=85)
                img_data = img_buffer.getvalue()
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Ошибка обработки изображения: {e}'
                }
            
            # Кодируем в base64
            image_data = base64.b64encode(img_data).decode()
            
            # Используем Gemini для анализа структуры
            if self.use_gemini and self.proxy_api_key:
                return self._analyze_structure_with_gemini(image_data, image_path.name)
            else:
                return {
                    'success': False,
                    'error': 'Gemini не настроен для анализа структуры'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка анализа структуры: {e}'
            }
    
    def _analyze_structure_with_gemini(self, image_data: str, image_name: str) -> Dict[str, Any]:
        """Анализ структуры документа с помощью Gemini"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.proxy_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.gemini_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Проанализируй структуру этого документа '{image_name}'. Определи тип документа, основные разделы, заголовки, таблицы, схемы. Ответь в формате JSON с полями: document_type, sections, headers, tables, diagrams."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800,
            "temperature": 0.1
        }
        
        response = requests.post(
            "https://api.proxyapi.ru/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            # Пытаемся распарсить JSON
            try:
                import json
                structure_data = json.loads(analysis_text)
                return {
                    'success': True,
                    'structure': structure_data,
                    'raw_analysis': analysis_text,
                    'model': self.gemini_model,
                    'provider': 'gpt-4o'
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'structure': {'document_type': 'unknown', 'sections': [], 'headers': []},
                    'raw_analysis': analysis_text,
                    'model': self.gemini_model,
                    'provider': 'gpt-4o'
                }
        else:
            raise Exception(f'Gemini API error: {response.status_code} - {response.text}')