"""
Vision Document Processing Module
Обработка изображений и документов с помощью LLaVA-Phi3
"""

import streamlit as st
import requests
import base64
from PIL import Image
import io
from typing import List, Dict, Optional, Union
import os
from pathlib import Path
import json
import logging
import sys

# Добавляем путь к конфигурации
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import MODELS, OLLAMA_BASE_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionProcessor:
    def __init__(self, ollama_base_url: str = None):
        self.ollama_base_url = ollama_base_url or OLLAMA_BASE_URL
        self.model_name = MODELS["vision"]
        
    def image_to_base64(self, image: Union[str, Path, Image.Image]) -> str:
        """Конвертация изображения в base64"""
        try:
            if isinstance(image, (str, Path)):
                with open(image, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            elif isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            else:
                raise ValueError("Неподдерживаемый тип изображения")
        except Exception as e:
            logger.error(f"Ошибка конвертации в base64: {e}")
            return ""
    
    def analyze_image_with_llava(self, image: Union[str, Path, Image.Image], 
                               prompt: str = None) -> Dict:
        """Анализ изображения с помощью LLaVA-Phi3"""
        try:
            # Конвертируем изображение в base64
            image_b64 = self.image_to_base64(image)
            if not image_b64:
                return {
                    'success': False,
                    'error': 'Не удалось конвертировать изображение в base64'
                }
            
            # Промпт по умолчанию для анализа документов
            if prompt is None:
                prompt = """Проанализируй это изображение документа. Извлеки и опиши:
1. Тип документа (договор, регламент, инструкция, отчет и т.д.)
2. Основные разделы и заголовки
3. Ключевые данные (даты, суммы, условия, ограничения)
4. Структуру документа
5. Любые таблицы, списки или важные детали

Отвечай на русском языке, будь подробным и структурированным."""
            
            # Подготавливаем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            }
            
            # Отправляем запрос
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'analysis': result.get('response', ''),
                    'model': self.model_name,
                    'prompt_used': prompt
                }
            else:
                return {
                    'success': False,
                    'error': f"Ошибка API: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_text_from_image_llava(self, image: Union[str, Path, Image.Image]) -> str:
        """Извлечение текста из изображения с помощью LLaVA"""
        try:
            prompt = """Извлеки весь текст с этого изображения. Воспроизведи текст точно как он написан, сохраняя:
- Структуру и форматирование
- Номера пунктов и разделов
- Таблицы (если есть)
- Даты, суммы, технические параметры

Отвечай только текстом, без дополнительных комментариев."""
            
            result = self.analyze_image_with_llava(image, prompt)
            if result['success']:
                return result['analysis']
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Ошибка извлечения текста: {e}")
            return ""
    
    def analyze_document_structure(self, image: Union[str, Path, Image.Image]) -> Dict:
        """Анализ структуры документа"""
        try:
            prompt = """Проанализируй структуру этого документа и верни результат в JSON формате:
{
    "document_type": "тип документа",
    "sections": [
        {"title": "заголовок раздела", "page": "номер страницы"},
        ...
    ],
    "key_info": {
        "dates": ["даты из документа"],
        "amounts": ["суммы и числа"],
        "conditions": ["условия и ограничения"]
    },
    "tables": ["описание таблиц если есть"],
    "summary": "краткое описание документа"
}"""
            
            result = self.analyze_image_with_llava(image, prompt)
            if result['success']:
                try:
                    # Пытаемся распарсить JSON из ответа
                    analysis_text = result['analysis']
                    # Ищем JSON в ответе
                    start_idx = analysis_text.find('{')
                    end_idx = analysis_text.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = analysis_text[start_idx:end_idx]
                        structure = json.loads(json_str)
                        return {
                            'success': True,
                            'structure': structure,
                            'raw_analysis': analysis_text
                        }
                except json.JSONDecodeError:
                    pass
                
                return {
                    'success': True,
                    'structure': None,
                    'raw_analysis': result['analysis']
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Ошибка анализа структуры: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_document_with_vision(self, file_path: str) -> Dict:
        """Обработка документа с помощью vision модели"""
        try:
            file_path = Path(file_path)
            
            # Проверяем, что это изображение
            if file_path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}:
                return {
                    'success': False,
                    'error': f'Неподдерживаемый формат: {file_path.suffix}'
                }
            
            # Анализируем изображение
            analysis_result = self.analyze_image_with_llava(file_path)
            if not analysis_result['success']:
                return analysis_result
            
            # Извлекаем текст
            text_content = self.extract_text_from_image_llava(file_path)
            
            # Анализируем структуру
            structure_result = self.analyze_document_structure(file_path)
            
            return {
                'success': True,
                'text_content': text_content,
                'analysis': analysis_result['analysis'],
                'structure': structure_result.get('structure') if structure_result['success'] else None,
                'extraction_method': 'llava_vision',
                'metadata': {
                    'original_file': str(file_path),
                    'file_type': file_path.suffix,
                    'file_size': file_path.stat().st_size,
                    'model_used': self.model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_model_availability(self) -> Dict:
        """Проверка доступности LLaVA модели"""
        try:
            # Проверяем список доступных моделей
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name in model_names:
                    return {
                        'available': True,
                        'model_name': self.model_name,
                        'all_models': model_names
                    }
                else:
                    return {
                        'available': False,
                        'model_name': self.model_name,
                        'all_models': model_names,
                        'message': f'Модель {self.model_name} не найдена. Доступные модели: {", ".join(model_names)}'
                    }
            else:
                return {
                    'available': False,
                    'error': f'Ошибка подключения к Ollama: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }
    
    def get_vision_info(self) -> Dict:
        """Получить информацию о vision системе"""
        model_status = self.check_model_availability()
        
        return {
            'ollama_url': self.ollama_base_url,
            'model_name': self.model_name,
            'model_available': model_status.get('available', False),
            'model_info': model_status,
            'supported_formats': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']
        }

