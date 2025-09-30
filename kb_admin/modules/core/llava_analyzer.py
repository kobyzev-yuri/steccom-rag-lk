"""
LLaVA Image Analyzer
Интеграция с LLaVA для анализа изображений и генерации описаний
"""

import streamlit as st
import requests
import base64
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import logging

class LLaVAAnalyzer:
    """Универсальный анализатор изображений с поддержкой Ollama и ProxyAPI"""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", 
                 use_proxy_api: bool = False, proxy_api_key: str = None,
                 proxy_api_provider: str = "openai"):
        self.ollama_base_url = ollama_base_url
        self.model_name = "llava:7b"  # Модель LLaVA для Ollama
        self.logger = logging.getLogger(__name__)
        
        # Настройки ProxyAPI
        self.use_proxy_api = use_proxy_api
        self.proxy_api_key = proxy_api_key
        self.proxy_api_provider = proxy_api_provider  # openai, anthropic, gemini
        
        # Модели для разных провайдеров
        self.proxy_models = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-7-sonnet-20250219", 
            "gemini": "gemini-1.5-pro"
        }
        
    def is_available(self) -> bool:
        """Проверка доступности анализатора изображений"""
        if self.use_proxy_api:
            return self._check_proxy_api_availability()
        else:
            return self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Проверка доступности Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                # Проверяем, есть ли модель LLaVA
                for model in models:
                    if 'llava' in model.get('name', '').lower():
                        return True
                return False
            return False
        except Exception as e:
            self.logger.warning(f"Ollama недоступен: {e}")
            return False
    
    def _check_proxy_api_availability(self) -> bool:
        """Проверка доступности ProxyAPI"""
        if not self.proxy_api_key:
            return False
        
        try:
            # Простой тест доступности API
            headers = {
                "Authorization": f"Bearer {self.proxy_api_key}",
                "Content-Type": "application/json"
            }
            
            # Тестируем разные провайдеры
            if self.proxy_api_provider == "openai":
                test_url = "https://api.proxyapi.ru/openai/v1/models"
            elif self.proxy_api_provider == "anthropic":
                test_url = "https://api.proxyapi.ru/anthropic/v1/messages"
            elif self.proxy_api_provider == "gemini":
                test_url = "https://api.proxyapi.ru/gemini/v1/models"
            else:
                return False
            
            response = requests.get(test_url, headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.warning(f"ProxyAPI недоступен: {e}")
            return False
    
    def analyze_image(self, image_path: Path, prompt: str = None) -> Dict:
        """Анализ изображения с помощью доступного анализатора"""
        if not self.is_available():
            error_msg = 'Анализатор изображений недоступен. '
            if self.use_proxy_api:
                error_msg += 'Проверьте настройки ProxyAPI и API ключ.'
            else:
                error_msg += 'Убедитесь, что Ollama запущен и модель llava загружена.'
            
            return {
                'success': False,
                'error': error_msg,
                'description': '',
                'analysis': ''
            }
        
        if self.use_proxy_api:
            return self._analyze_with_proxy_api(image_path, prompt)
        else:
            return self._analyze_with_ollama(image_path, prompt)
    
    def _analyze_with_ollama(self, image_path: Path, prompt: str = None) -> Dict:
        """Анализ изображения через Ollama"""
        try:
            # Читаем изображение и кодируем в base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Формируем промпт для анализа
            if prompt is None:
                prompt = """Проанализируй это изображение и дай подробное описание на русском языке. 
                Опиши что изображено, какие объекты, текст, схемы, диаграммы или другие элементы видны. 
                Если есть текст, попробуй его прочитать и перевести. 
                Оцени важность изображения для понимания документа."""
            
            # Подготавливаем данные для запроса
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '').strip()
                
                # Разделяем описание и анализ
                description, analysis = self._parse_analysis(analysis_text)
                
                return {
                    'success': True,
                    'error': None,
                    'description': description,
                    'analysis': analysis,
                    'full_response': analysis_text,
                    'model_used': self.model_name,
                    'provider': 'ollama'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ошибка API Ollama: {response.status_code}',
                    'description': '',
                    'analysis': ''
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа изображения через Ollama {image_path}: {e}")
            return {
                'success': False,
                'error': f'Ошибка анализа Ollama: {str(e)}',
                'description': '',
                'analysis': ''
            }
    
    def _analyze_with_proxy_api(self, image_path: Path, prompt: str = None) -> Dict:
        """Анализ изображения через ProxyAPI"""
        try:
            # Читаем изображение и кодируем в base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Определяем MIME тип
            mime_type = "image/jpeg"
            if image_path.suffix.lower() in ['.png']:
                mime_type = "image/png"
            elif image_path.suffix.lower() in ['.gif']:
                mime_type = "image/gif"
            elif image_path.suffix.lower() in ['.webp']:
                mime_type = "image/webp"
            
            # Формируем промпт для анализа
            if prompt is None:
                prompt = """Проанализируй это изображение и дай подробное описание на русском языке. 
                Опиши что изображено, какие объекты, текст, схемы, диаграммы или другие элементы видны. 
                Если есть текст, попробуй его прочитать и перевести. 
                Оцени важность изображения для понимания документа."""
            
            headers = {
                "Authorization": f"Bearer {self.proxy_api_key}",
                "Content-Type": "application/json"
            }
            
            model_name = self.proxy_models[self.proxy_api_provider]
            
            if self.proxy_api_provider == "openai":
                return self._analyze_with_openai_api(image_data, mime_type, prompt, headers, model_name)
            elif self.proxy_api_provider == "anthropic":
                return self._analyze_with_anthropic_api(image_data, mime_type, prompt, headers, model_name)
            elif self.proxy_api_provider == "gemini":
                return self._analyze_with_gemini_api(image_data, mime_type, prompt, headers, model_name)
            else:
                return {
                    'success': False,
                    'error': f'Неподдерживаемый провайдер: {self.proxy_api_provider}',
                    'description': '',
                    'analysis': ''
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа изображения через ProxyAPI {image_path}: {e}")
            return {
                'success': False,
                'error': f'Ошибка анализа ProxyAPI: {str(e)}',
                'description': '',
                'analysis': ''
            }
    
    def _parse_analysis(self, analysis_text: str) -> Tuple[str, str]:
        """Разбор ответа LLaVA на описание и анализ"""
        # Простое разделение: первые 2-3 предложения - описание, остальное - анализ
        sentences = analysis_text.split('. ')
        
        if len(sentences) <= 2:
            return analysis_text, ""
        
        # Первые 2-3 предложения как описание
        description_sentences = sentences[:min(3, len(sentences))]
        description = '. '.join(description_sentences)
        if not description.endswith('.'):
            description += '.'
        
        # Остальное как анализ
        analysis_sentences = sentences[3:]
        analysis = '. '.join(analysis_sentences)
        if not analysis.endswith('.'):
            analysis += '.'
        
        return description, analysis
    
    def _analyze_with_openai_api(self, image_data: str, mime_type: str, prompt: str, headers: dict, model_name: str) -> Dict:
        """Анализ через OpenAI API через ProxyAPI"""
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.proxyapi.ru/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['choices'][0]['message']['content'].strip()
                
                description, analysis = self._parse_analysis(analysis_text)
                
                return {
                    'success': True,
                    'error': None,
                    'description': description,
                    'analysis': analysis,
                    'full_response': analysis_text,
                    'model_used': model_name,
                    'provider': 'openai_proxy'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ошибка OpenAI API: {response.status_code} - {response.text}',
                    'description': '',
                    'analysis': ''
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка OpenAI API: {str(e)}',
                'description': '',
                'analysis': ''
            }
    
    def _analyze_with_anthropic_api(self, image_data: str, mime_type: str, prompt: str, headers: dict, model_name: str) -> Dict:
        """Анализ через Anthropic Claude API через ProxyAPI"""
        try:
            payload = {
                "model": model_name,
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                "https://api.proxyapi.ru/anthropic/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['content'][0]['text'].strip()
                
                description, analysis = self._parse_analysis(analysis_text)
                
                return {
                    'success': True,
                    'error': None,
                    'description': description,
                    'analysis': analysis,
                    'full_response': analysis_text,
                    'model_used': model_name,
                    'provider': 'anthropic_proxy'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ошибка Anthropic API: {response.status_code} - {response.text}',
                    'description': '',
                    'analysis': ''
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка Anthropic API: {str(e)}',
                'description': '',
                'analysis': ''
            }
    
    def _analyze_with_gemini_api(self, image_data: str, mime_type: str, prompt: str, headers: dict, model_name: str) -> Dict:
        """Анализ через Google Gemini API через ProxyAPI"""
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(
                f"https://api.proxyapi.ru/gemini/v1/models/{model_name}:generateContent",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                description, analysis = self._parse_analysis(analysis_text)
                
                return {
                    'success': True,
                    'error': None,
                    'description': description,
                    'analysis': analysis,
                    'full_response': analysis_text,
                    'model_used': model_name,
                    'provider': 'gemini_proxy'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ошибка Gemini API: {response.status_code} - {response.text}',
                    'description': '',
                    'analysis': ''
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка Gemini API: {str(e)}',
                'description': '',
                'analysis': ''
            }
    
    def batch_analyze_images(self, image_paths: List[Path], 
                           progress_callback=None) -> List[Dict]:
        """Пакетный анализ изображений"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i, len(image_paths), f"Анализ {image_path.name}")
            
            result = self.analyze_image(image_path)
            result['image_path'] = str(image_path)
            result['image_name'] = image_path.name
            results.append(result)
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
        
        if progress_callback:
            progress_callback(len(image_paths), len(image_paths), "Анализ завершен")
        
        return results
    
    def get_model_info(self) -> Dict:
        """Получить информацию о доступных моделях"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llava_models = [model for model in models if 'llava' in model.get('name', '').lower()]
                
                return {
                    'available': True,
                    'llava_models': llava_models,
                    'current_model': self.model_name
                }
            else:
                return {'available': False, 'error': f'Ошибка API: {response.status_code}'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def set_model(self, model_name: str) -> bool:
        """Установить модель LLaVA"""
        try:
            # Проверяем, что модель доступна
            model_info = self.get_model_info()
            if not model_info['available']:
                return False
            
            available_models = [model['name'] for model in model_info['llava_models']]
            if model_name in available_models:
                self.model_name = model_name
                return True
            else:
                self.logger.warning(f"Модель {model_name} недоступна. Доступные: {available_models}")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка установки модели: {e}")
            return False

class ImageExtractor:
    """Извлечение изображений из PDF документов"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def extract_images_from_pdf(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """Извлечение изображений из PDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    # Получаем изображение
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Пропускаем изображения с альфа-каналом
                    if pix.n - pix.alpha < 4:
                        # Сохраняем изображение
                        image_name = f"{pdf_path.stem}_page_{page_num + 1}_img_{img_index + 1}.png"
                        image_path = output_dir / image_name
                        
                        if pix.alpha:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        
                        pix.save(str(image_path))
                        extracted_images.append(image_path)
                        pix = None
            
            doc.close()
            return extracted_images
            
        except ImportError:
            raise ImportError("PyMuPDF не установлен. Установите: pip install PyMuPDF")
        except Exception as e:
            raise Exception(f"Ошибка извлечения изображений: {e}")
    
    def extract_images_from_document(self, doc_path: Path, output_dir: Path) -> List[Path]:
        """Извлечение изображений из документа (универсальный метод)"""
        if not doc_path.exists():
            raise FileNotFoundError(f"Файл не найден: {doc_path}")
        
        if doc_path.suffix.lower() == '.pdf':
            return self.extract_images_from_pdf(doc_path, output_dir)
        else:
            # Для других форматов пока не реализовано
            return []
    
    def is_image_file(self, file_path: Path) -> bool:
        """Проверка, является ли файл изображением"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        return file_path.suffix.lower() in image_extensions
