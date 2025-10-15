#!/usr/bin/env python3
"""
Скрипт для восстановления создания KB с использованием Gemini
Восстанавливает функциональность умного библиотекаря с Gemini для анализа документов
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules"))
sys.path.insert(0, str(current_dir.parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_kb_restoration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeminiKBManager:
    """Менеджер для восстановления создания KB с Gemini"""
    
    def __init__(self):
        self.vision_processor = None
        self.smart_librarian = None
        self.kb_manager = None
        
        # Инициализация компонентов
        self._initialize_components()
    
    def _initialize_components(self):
        """Инициализация компонентов системы"""
        try:
            # Импортируем необходимые модули
            from modules.documents.vision_processor import VisionProcessor
            from modules.core.smart_document_agent import SmartLibrarian
            from modules.core.knowledge_manager import KnowledgeBaseManager
            from modules.documents.pdf_processor import PDFProcessor
            
            # Инициализируем компоненты
            self.vision_processor = VisionProcessor()
            self.kb_manager = KnowledgeBaseManager()
            pdf_processor = PDFProcessor()
            self.smart_librarian = SmartLibrarian(self.kb_manager, pdf_processor)
            
            logger.info("✅ Компоненты системы инициализированы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def check_gemini_availability(self) -> Dict[str, Any]:
        """Проверка доступности Gemini"""
        logger.info("🔍 Проверяем доступность Gemini...")
        
        try:
            if not self.vision_processor:
                return {
                    'available': False,
                    'error': 'VisionProcessor не инициализирован'
                }
            
            # Проверяем настройки Gemini
            gemini_status = self.vision_processor.check_model_availability()
            
            if gemini_status.get('available'):
                logger.info(f"✅ {gemini_status.get('message', 'Gemini доступен')}")
                return gemini_status
            else:
                logger.warning(f"⚠️ {gemini_status.get('message', 'Gemini недоступен')}")
                return gemini_status
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки Gemini: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def test_gemini_analysis(self, test_image_path: Optional[Path] = None) -> Dict[str, Any]:
        """Тестирование анализа изображений через Gemini"""
        logger.info("🧪 Тестируем анализ изображений через Gemini...")
        
        try:
            if not test_image_path:
                # Создаем тестовое изображение
                test_image_path = self._create_test_image()
            
            if not test_image_path.exists():
                return {
                    'success': False,
                    'error': f'Тестовое изображение не найдено: {test_image_path}'
                }
            
            # Анализируем изображение
            analysis_result = self.vision_processor.analyze_image_with_gemini(test_image_path)
            
            if analysis_result.get('success'):
                logger.info("✅ Анализ изображения через Gemini успешен")
                return {
                    'success': True,
                    'analysis': analysis_result.get('analysis', ''),
                    'model': analysis_result.get('model', ''),
                    'provider': analysis_result.get('provider', '')
                }
            else:
                logger.warning(f"⚠️ Ошибка анализа: {analysis_result.get('error', 'Неизвестная ошибка')}")
                return analysis_result
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования Gemini: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_test_image(self) -> Path:
        """Создание тестового изображения для проверки"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Создаем простое тестовое изображение
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Добавляем текст
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            text = "Тестовый документ\nСпутниковая связь VSAT\nТехнические характеристики\nДата: 2025"
            draw.text((50, 50), text, font=font, fill='black')
            
            # Сохраняем изображение
            test_image_path = current_dir / "test_document.png"
            img.save(test_image_path)
            
            logger.info(f"✅ Создано тестовое изображение: {test_image_path}")
            return test_image_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестового изображения: {e}")
            raise
    
    def restore_smart_librarian_functionality(self) -> Dict[str, Any]:
        """Восстановление функциональности умного библиотекаря"""
        logger.info("🔧 Восстанавливаем функциональность умного библиотекаря...")
        
        try:
            # Проверяем компоненты
            if not self.smart_librarian:
                return {
                    'success': False,
                    'error': 'SmartLibrarian не инициализирован'
                }
            
            # Тестируем основные функции
            test_results = {
                'document_analysis': False,
                'image_processing': False,
                'kb_creation': False,
                'gemini_integration': False
            }
            
            # Тест 1: Анализ документа
            try:
                # Создаем тестовый документ
                test_doc_path = self._create_test_document()
                analysis = self.smart_librarian.analyze_document(test_doc_path)
                
                if analysis and 'file_name' in analysis:
                    test_results['document_analysis'] = True
                    logger.info("✅ Анализ документов работает")
                else:
                    logger.warning("⚠️ Анализ документов не работает корректно")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка тестирования анализа документов: {e}")
            
            # Тест 2: Обработка изображений
            try:
                test_image_path = self._create_test_image()
                image_analysis = self.vision_processor.analyze_image_with_gemini(test_image_path)
                
                if image_analysis.get('success'):
                    test_results['image_processing'] = True
                    logger.info("✅ Обработка изображений работает")
                else:
                    logger.warning("⚠️ Обработка изображений не работает")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка тестирования обработки изображений: {e}")
            
            # Тест 3: Создание KB
            try:
                test_kb_id = self.kb_manager.create_knowledge_base(
                    name="Тестовая KB для восстановления",
                    description="Тестовая база знаний для проверки функциональности",
                    category="Тестирование",
                    created_by="gemini_restoration"
                )
                
                if test_kb_id:
                    test_results['kb_creation'] = True
                    logger.info(f"✅ Создание KB работает (ID: {test_kb_id})")
                    
                    # Удаляем тестовую KB
                    self.kb_manager.delete_knowledge_base(test_kb_id)
                else:
                    logger.warning("⚠️ Создание KB не работает")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка тестирования создания KB: {e}")
            
            # Тест 4: Интеграция с Gemini
            gemini_status = self.check_gemini_availability()
            if gemini_status.get('available'):
                test_results['gemini_integration'] = True
                logger.info("✅ Интеграция с Gemini работает")
            else:
                logger.warning("⚠️ Интеграция с Gemini не работает")
            
            # Подсчитываем общий результат
            working_components = sum(test_results.values())
            total_components = len(test_results)
            success_rate = working_components / total_components
            
            return {
                'success': success_rate > 0.5,
                'success_rate': success_rate,
                'working_components': working_components,
                'total_components': total_components,
                'test_results': test_results,
                'recommendations': self._generate_recommendations(test_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления функциональности: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_test_document(self) -> Path:
        """Создание тестового документа"""
        try:
            test_doc_path = current_dir / "test_document.txt"
            
            test_content = """
ТЕХНИЧЕСКИЙ РЕГЛАМЕНТ
Спутниковая связь VSAT

1. ОБЩИЕ ПОЛОЖЕНИЯ
1.1. Настоящий регламент определяет порядок работы с системой спутниковой связи VSAT.
1.2. Система предназначена для обеспечения связи в удаленных районах.

2. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
2.1. Частота работы: 14/12 ГГц
2.2. Мощность передатчика: до 2 Вт
2.3. Диаметр антенны: 1.2-2.4 м

3. ПРОЦЕДУРЫ УСТАНОВКИ
3.1. Выбор места установки антенны
3.2. Настройка оборудования
3.3. Тестирование связи

Дата: 2025-01-08
Версия: 1.0
            """
            
            with open(test_doc_path, 'w', encoding='utf-8') as f:
                f.write(test_content.strip())
            
            logger.info(f"✅ Создан тестовый документ: {test_doc_path}")
            return test_doc_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестового документа: {e}")
            raise
    
    def _generate_recommendations(self, test_results: Dict[str, bool]) -> List[str]:
        """Генерация рекомендаций на основе результатов тестирования"""
        recommendations = []
        
        if not test_results.get('gemini_integration'):
            recommendations.append("🔧 Настройте PROXYAPI_KEY для работы с Gemini")
        
        if not test_results.get('document_analysis'):
            recommendations.append("🔧 Проверьте инициализацию SmartLibrarian")
        
        if not test_results.get('image_processing'):
            recommendations.append("🔧 Проверьте настройки VisionProcessor")
        
        if not test_results.get('kb_creation'):
            recommendations.append("🔧 Проверьте подключение к базе данных")
        
        if not recommendations:
            recommendations.append("✅ Все компоненты работают корректно")
        
        return recommendations
    
    def create_demo_kb_with_gemini(self) -> Dict[str, Any]:
        """Создание демонстрационной KB с использованием Gemini"""
        logger.info("🎯 Создаем демонстрационную KB с Gemini...")
        
        try:
            # Создаем KB
            kb_id = self.kb_manager.create_knowledge_base(
                name="Демонстрационная KB с Gemini",
                description="База знаний, созданная с использованием анализа Gemini",
                category="Демонстрация",
                created_by="gemini_demo"
            )
            
            if not kb_id:
                return {
                    'success': False,
                    'error': 'Не удалось создать KB'
                }
            
            # Создаем тестовый документ с изображением
            test_doc_path = self._create_test_document()
            test_image_path = self._create_test_image()
            
            # Анализируем документ
            analysis = self.smart_librarian.analyze_document(test_doc_path)
            
            # Добавляем документ в KB
            doc_id = self.kb_manager.add_document_to_kb(
                kb_id=kb_id,
                title="Тестовый документ с анализом Gemini",
                file_path=str(test_doc_path),
                content_type="text/plain",
                file_size=test_doc_path.stat().st_size,
                created_by="gemini_demo",
                metadata=json.dumps(analysis, ensure_ascii=False) if analysis else None
            )
            
            # Анализируем изображение через Gemini
            if test_image_path.exists():
                image_analysis = self.vision_processor.analyze_image_with_gemini(test_image_path)
                
                if image_analysis.get('success'):
                    # Добавляем изображение в KB
                    self.kb_manager.add_image(
                        kb_id=kb_id,
                        image_path=str(test_image_path),
                        image_name=test_image_path.name,
                        image_description=image_analysis.get('analysis', ''),
                        llava_analysis=image_analysis.get('analysis', '')
                    )
            
            # Очищаем тестовые файлы
            try:
                test_doc_path.unlink()
                test_image_path.unlink()
            except:
                pass
            
            return {
                'success': True,
                'kb_id': kb_id,
                'doc_id': doc_id,
                'message': f'Демонстрационная KB создана с ID: {kb_id}'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания демонстрационной KB: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """Основная функция восстановления"""
    print("🤖 Восстановление создания KB с использованием Gemini")
    print("=" * 60)
    
    try:
        # Создаем менеджер
        manager = GeminiKBManager()
        
        # Проверяем доступность Gemini
        print("\n🔍 Проверка доступности Gemini...")
        gemini_status = manager.check_gemini_availability()
        print(f"Статус: {'✅ Доступен' if gemini_status.get('available') else '❌ Недоступен'}")
        if gemini_status.get('message'):
            print(f"Сообщение: {gemini_status['message']}")
        
        # Восстанавливаем функциональность
        print("\n🔧 Восстановление функциональности...")
        restoration_result = manager.restore_smart_librarian_functionality()
        
        print(f"\n📊 Результаты восстановления:")
        print(f"  Успешность: {restoration_result.get('success_rate', 0):.1%}")
        print(f"  Работающих компонентов: {restoration_result.get('working_components', 0)}/{restoration_result.get('total_components', 0)}")
        
        # Показываем результаты тестов
        test_results = restoration_result.get('test_results', {})
        print(f"\n🧪 Результаты тестирования:")
        for component, status in test_results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component.replace('_', ' ').title()}")
        
        # Показываем рекомендации
        recommendations = restoration_result.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Рекомендации:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        # Создаем демонстрационную KB если все работает
        if restoration_result.get('success'):
            print(f"\n🎯 Создание демонстрационной KB...")
            demo_result = manager.create_demo_kb_with_gemini()
            
            if demo_result.get('success'):
                print(f"✅ {demo_result.get('message', 'KB создана успешно')}")
            else:
                print(f"❌ Ошибка создания демо KB: {demo_result.get('error', 'Неизвестная ошибка')}")
        
        print("\n" + "=" * 60)
        print("🎉 Восстановление завершено!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Восстановление прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()







