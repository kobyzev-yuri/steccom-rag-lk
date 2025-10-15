#!/usr/bin/env python3
"""
Скрипт для анализа изображений в PDF файле
Тестирует LLaVA и Gemini на реальном PDF с изображениями
"""

import sys
import os
import time
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
        logging.FileHandler('pdf_images_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PDFImagesAnalyzer:
    """Анализатор изображений в PDF с использованием LLaVA и Gemini"""
    
    def __init__(self):
        self.vision_processor = None
        self.llava_analyzer = None
        self.image_extractor = None
        
        # Инициализация компонентов
        self._initialize_components()
    
    def _initialize_components(self):
        """Инициализация компонентов для анализа"""
        try:
            # Импортируем VisionProcessor (Gemini)
            from modules.documents.vision_processor import VisionProcessor
            self.vision_processor = VisionProcessor()
            logger.info("✅ VisionProcessor (Gemini) инициализирован")
            
            # Импортируем LLaVAAnalyzer (Ollama)
            import sys
            sys.path.append(str(current_dir / "modules" / "core"))
            from llava_analyzer import LLaVAAnalyzer
            self.llava_analyzer = LLaVAAnalyzer()
            # Устанавливаем правильную модель
            self.llava_analyzer.set_model("llava-phi3:latest")
            logger.info("✅ LLaVAAnalyzer (Ollama) инициализирован")
            
            # Импортируем ImageExtractor
            from llava_analyzer import ImageExtractor
            self.image_extractor = ImageExtractor()
            logger.info("✅ ImageExtractor инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def extract_images_from_pdf(self, pdf_path: Path) -> List[Path]:
        """Извлечение изображений из PDF"""
        logger.info(f"📄 Извлекаем изображения из PDF: {pdf_path.name}")
        
        try:
            # Создаем директорию для извлеченных изображений
            output_dir = current_dir / "extracted_images" / pdf_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Извлекаем изображения напрямую через PyMuPDF
            import fitz
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    # Получаем изображение
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Конвертируем CMYK в RGB и обрабатываем альфа-канал
                    if pix.colorspace and pix.colorspace.name == 'DeviceCMYK':
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    elif pix.alpha:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                    # Сохраняем изображение
                    image_name = f"page_{page_num + 1}_img_{img_index + 1}.png"
                    image_path = output_dir / image_name
                    
                    pix.save(str(image_path))
                    extracted_images.append(image_path)
                    pix = None
            
            doc.close()
            
            logger.info(f"✅ Извлечено {len(extracted_images)} изображений")
            for img_path in extracted_images:
                logger.info(f"  📷 {img_path.name}")
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения изображений: {e}")
            return []
    
    def analyze_image_with_both(self, image_path: Path) -> Dict[str, Any]:
        """Анализ изображения с помощью LLaVA и Gemini"""
        logger.info(f"🔍 Анализируем изображение: {image_path.name}")
        
        results = {
            'image_path': str(image_path),
            'image_name': image_path.name,
            'image_size': image_path.stat().st_size,
            'llava_result': None,
            'gemini_result': None,
            'comparison': {}
        }
        
        # Анализ с помощью LLaVA
        if self.llava_analyzer and self.llava_analyzer.is_available():
            try:
                logger.info("  🦙 Анализ с помощью LLaVA...")
                start_time = time.time()
                
                # Специальный промпт для технических документов
                prompt = """Проанализируй это изображение из технического документа о спутниковой связи. 

Опиши подробно:
1. Что изображено на схеме/диаграмме
2. Какие технические элементы видны
3. Какие параметры, характеристики или данные указаны
4. Структуру и связи между элементами
5. Любые важные технические детали

Отвечай на русском языке, будь максимально подробным и технически точным."""
                
                llava_result = self.llava_analyzer.analyze_image(image_path, prompt)
                llava_time = time.time() - start_time
                
                results['llava_result'] = {
                    'success': llava_result.get('success', False),
                    'analysis': llava_result.get('analysis', ''),
                    'description': llava_result.get('description', ''),
                    'full_response': llava_result.get('full_response', ''),
                    'error': llava_result.get('error', ''),
                    'response_time': llava_time,
                    'model': llava_result.get('model_used', ''),
                    'provider': llava_result.get('provider', '')
                }
                
                logger.info(f"    LLaVA: {'✅' if results['llava_result']['success'] else '❌'} ({llava_time:.2f}с)")
                
            except Exception as e:
                results['llava_result'] = {
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                }
                logger.error(f"    ❌ Ошибка LLaVA: {e}")
        else:
            logger.warning("  ⚠️ LLaVA недоступен")
        
        # Анализ с помощью Gemini
        if self.vision_processor:
            try:
                logger.info("  🤖 Анализ с помощью Gemini...")
                start_time = time.time()
                
                gemini_result = self.vision_processor.analyze_image_with_gemini(image_path)
                gemini_time = time.time() - start_time
                
                results['gemini_result'] = {
                    'success': gemini_result.get('success', False),
                    'analysis': gemini_result.get('analysis', ''),
                    'error': gemini_result.get('error', ''),
                    'response_time': gemini_time,
                    'model': gemini_result.get('model', ''),
                    'provider': gemini_result.get('provider', '')
                }
                
                logger.info(f"    Gemini: {'✅' if results['gemini_result']['success'] else '❌'} ({gemini_time:.2f}с)")
                
            except Exception as e:
                results['gemini_result'] = {
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                }
                logger.error(f"    ❌ Ошибка Gemini: {e}")
        else:
            logger.warning("  ⚠️ Gemini недоступен")
        
        # Сравнение результатов
        if results['llava_result'] and results['gemini_result']:
            results['comparison'] = self._compare_analysis_results(
                results['llava_result'], 
                results['gemini_result']
            )
        
        return results
    
    def _compare_analysis_results(self, llava_result: Dict, gemini_result: Dict) -> Dict[str, Any]:
        """Сравнение результатов анализа LLaVA и Gemini"""
        comparison = {
            'both_successful': llava_result['success'] and gemini_result['success'],
            'llava_faster': llava_result['response_time'] < gemini_result['response_time'],
            'speed_difference': abs(llava_result['response_time'] - gemini_result['response_time']),
            'quality_metrics': {}
        }
        
        if comparison['both_successful']:
            # Сравнение качества по длине и содержанию
            llava_text = llava_result['analysis']
            gemini_text = gemini_result['analysis']
            
            comparison['quality_metrics'] = {
                'llava_length': len(llava_text),
                'gemini_length': len(gemini_text),
                'length_ratio': len(llava_text) / len(gemini_text) if len(gemini_text) > 0 else 0,
                'llava_has_technical_terms': any(term in llava_text.lower() for term in 
                    ['схема', 'диаграмма', 'параметр', 'характеристика', 'технический', 'система']),
                'gemini_has_technical_terms': any(term in gemini_text.lower() for term in 
                    ['схема', 'диаграмма', 'параметр', 'характеристика', 'технический', 'система'])
            }
            
            # Определяем лучший результат
            if comparison['quality_metrics']['llava_length'] > comparison['quality_metrics']['gemini_length'] * 1.2:
                comparison['better_analysis'] = 'llava'
            elif comparison['quality_metrics']['gemini_length'] > comparison['quality_metrics']['llava_length'] * 1.2:
                comparison['better_analysis'] = 'gemini'
            else:
                comparison['better_analysis'] = 'similar'
        
        return comparison
    
    def analyze_pdf_images(self, pdf_path: Path) -> Dict[str, Any]:
        """Полный анализ изображений в PDF"""
        logger.info(f"🚀 Начинаем анализ PDF: {pdf_path.name}")
        
        if not pdf_path.exists():
            return {
                'success': False,
                'error': f'PDF файл не найден: {pdf_path}',
                'results': []
            }
        
        # Извлекаем изображения
        extracted_images = self.extract_images_from_pdf(pdf_path)
        
        if not extracted_images:
            return {
                'success': False,
                'error': 'Не удалось извлечь изображения из PDF',
                'results': []
            }
        
        # Анализируем каждое изображение
        analysis_results = []
        total_llava_time = 0
        total_gemini_time = 0
        successful_llava = 0
        successful_gemini = 0
        
        for i, image_path in enumerate(extracted_images):
            logger.info(f"\n📷 Изображение {i+1}/{len(extracted_images)}: {image_path.name}")
            
            result = self.analyze_image_with_both(image_path)
            analysis_results.append(result)
            
            # Подсчитываем статистику
            if result['llava_result'] and result['llava_result']['success']:
                total_llava_time += result['llava_result']['response_time']
                successful_llava += 1
            
            if result['gemini_result'] and result['gemini_result']['success']:
                total_gemini_time += result['gemini_result']['response_time']
                successful_gemini += 1
        
        # Анализ результатов
        summary = self._analyze_results(analysis_results, successful_llava, successful_gemini, 
                                      total_llava_time, total_gemini_time)
        
        # Сохраняем результаты
        self._save_results(summary, analysis_results, pdf_path)
        
        return {
            'success': True,
            'pdf_path': str(pdf_path),
            'total_images': len(extracted_images),
            'summary': summary,
            'detailed_results': analysis_results
        }
    
    def _analyze_results(self, results: List[Dict], successful_llava: int, successful_gemini: int,
                        total_llava_time: float, total_gemini_time: float) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        total_images = len(results)
        
        summary = {
            'test_date': datetime.now().isoformat(),
            'total_images': total_images,
            'llava_metrics': {
                'successful_analyses': successful_llava,
                'success_rate': successful_llava / total_images if total_images > 0 else 0,
                'avg_response_time': total_llava_time / successful_llava if successful_llava > 0 else 0,
                'total_time': total_llava_time
            },
            'gemini_metrics': {
                'successful_analyses': successful_gemini,
                'success_rate': successful_gemini / total_images if total_images > 0 else 0,
                'avg_response_time': total_gemini_time / successful_gemini if successful_gemini > 0 else 0,
                'total_time': total_gemini_time
            },
            'comparison': {
                'llava_better_success': successful_llava > successful_gemini,
                'gemini_better_success': successful_gemini > successful_llava,
                'llava_faster': total_llava_time < total_gemini_time,
                'gemini_faster': total_gemini_time < total_llava_time
            },
            'recommendations': []
        }
        
        # Генерируем рекомендации
        if successful_llava > successful_gemini:
            summary['recommendations'].append("LLaVA показывает лучшую надежность")
        elif successful_gemini > successful_llava:
            summary['recommendations'].append("Gemini показывает лучшую надежность")
        
        if total_llava_time < total_gemini_time * 0.8:
            summary['recommendations'].append("LLaVA значительно быстрее")
        elif total_gemini_time < total_llava_time * 0.8:
            summary['recommendations'].append("Gemini значительно быстрее")
        
        if successful_llava > 0 and successful_gemini > 0:
            summary['recommendations'].append("Обе системы работают - можно использовать любую")
        elif successful_llava > 0:
            summary['recommendations'].append("Рекомендуется использовать LLaVA")
        elif successful_gemini > 0:
            summary['recommendations'].append("Рекомендуется использовать Gemini")
        else:
            summary['recommendations'].append("Проверьте настройки обеих систем")
        
        return summary
    
    def _save_results(self, summary: Dict, results: List[Dict], pdf_path: Path):
        """Сохранение результатов анализа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"pdf_images_analysis_{pdf_path.stem}_{timestamp}.json"
        
        full_results = {
            'summary': summary,
            'detailed_results': results,
            'pdf_info': {
                'name': pdf_path.name,
                'size': pdf_path.stat().st_size,
                'path': str(pdf_path)
            }
        }
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Результаты сохранены в {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")
    
    def print_summary(self, analysis: Dict):
        """Вывод краткого отчета"""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ ОБ АНАЛИЗЕ ИЗОБРАЖЕНИЙ В PDF")
        print("="*60)
        
        print(f"📅 Дата анализа: {analysis['summary']['test_date']}")
        print(f"📄 PDF файл: {analysis['pdf_path']}")
        print(f"🖼️ Всего изображений: {analysis['total_images']}")
        
        # Метрики LLaVA
        llava_metrics = analysis['summary']['llava_metrics']
        print(f"\n🦙 LLAVA РЕЗУЛЬТАТЫ:")
        print(f"  Успешных анализов: {llava_metrics['successful_analyses']}")
        print(f"  Успешность: {llava_metrics['success_rate']:.1%}")
        print(f"  Среднее время: {llava_metrics['avg_response_time']:.2f}с")
        print(f"  Общее время: {llava_metrics['total_time']:.2f}с")
        
        # Метрики Gemini
        gemini_metrics = analysis['summary']['gemini_metrics']
        print(f"\n🤖 GEMINI РЕЗУЛЬТАТЫ:")
        print(f"  Успешных анализов: {gemini_metrics['successful_analyses']}")
        print(f"  Успешность: {gemini_metrics['success_rate']:.1%}")
        print(f"  Среднее время: {gemini_metrics['avg_response_time']:.2f}с")
        print(f"  Общее время: {gemini_metrics['total_time']:.2f}с")
        
        # Сравнение
        comparison = analysis['summary']['comparison']
        print(f"\n⚖️ СРАВНЕНИЕ:")
        if comparison['llava_better_success']:
            print("  🥇 LLaVA более надежен")
        elif comparison['gemini_better_success']:
            print("  🥇 Gemini более надежен")
        else:
            print("  🤝 Надежность примерно одинакова")
        
        if comparison['llava_faster']:
            print("  ⚡ LLaVA быстрее")
        elif comparison['gemini_faster']:
            print("  ⚡ Gemini быстрее")
        else:
            print("  ⚖️ Скорость примерно одинакова")
        
        # Рекомендации
        recommendations = analysis['summary']['recommendations']
        if recommendations:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("="*60)

def main():
    """Основная функция"""
    print("🔍 Анализ изображений в PDF с помощью LLaVA и Gemini")
    print("=" * 60)
    
    # Путь к PDF файлу
    pdf_path = Path("/mnt/ai/cnn/steccom-rag-lk/data/uploads/Access-SkyEdge-II--170414-FINAL.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF файл не найден: {pdf_path}")
        print("Убедитесь, что файл существует в указанном пути")
        return 1
    
    try:
        analyzer = PDFImagesAnalyzer()
        analysis = analyzer.analyze_pdf_images(pdf_path)
        
        if analysis['success']:
            analyzer.print_summary(analysis)
            print(f"\n🎉 Анализ завершен успешно!")
            print(f"📄 Обработано изображений: {analysis['total_images']}")
        else:
            print(f"❌ Ошибка анализа: {analysis['error']}")
            return 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Анализ прерван пользователем")
        return 1
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
