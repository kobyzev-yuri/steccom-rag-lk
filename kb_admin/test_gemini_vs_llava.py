#!/usr/bin/env python3
"""
Скрипт для тестирования замены Gemini на Ollama LLaVA
Сравнивает производительность и качество обработки изображений
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
        logging.FileHandler('gemini_vs_llava_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeminiVsLLaVATester:
    """Тестер для сравнения Gemini и LLaVA"""
    
    def __init__(self):
        self.test_results = []
        self.vision_processor = None
        self.llava_analyzer = None
        
        # Инициализация компонентов
        self._initialize_components()
    
    def _initialize_components(self):
        """Инициализация компонентов для тестирования"""
        try:
            # Импортируем VisionProcessor (Gemini)
            from modules.documents.vision_processor import VisionProcessor
            self.vision_processor = VisionProcessor()
            logger.info("✅ VisionProcessor (Gemini) инициализирован")
            
            # Импортируем LLaVAAnalyzer (Ollama)
            from modules.core.llava_analyzer import LLaVAAnalyzer
            self.llava_analyzer = LLaVAAnalyzer()
            logger.info("✅ LLaVAAnalyzer (Ollama) инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def check_availability(self) -> Dict[str, Any]:
        """Проверка доступности обеих систем"""
        logger.info("🔍 Проверяем доступность систем...")
        
        results = {
            'gemini_available': False,
            'llava_available': False,
            'gemini_error': None,
            'llava_error': None
        }
        
        # Проверяем Gemini
        try:
            gemini_status = self.vision_processor.check_model_availability()
            results['gemini_available'] = gemini_status.get('available', False)
            if not results['gemini_available']:
                results['gemini_error'] = gemini_status.get('message', 'Неизвестная ошибка')
            logger.info(f"Gemini: {'✅ Доступен' if results['gemini_available'] else '❌ Недоступен'}")
        except Exception as e:
            results['gemini_error'] = str(e)
            logger.error(f"❌ Ошибка проверки Gemini: {e}")
        
        # Проверяем LLaVA
        try:
            results['llava_available'] = self.llava_analyzer.is_available()
            if not results['llava_available']:
                results['llava_error'] = "LLaVA недоступен - проверьте Ollama и модель llava"
            logger.info(f"LLaVA: {'✅ Доступен' if results['llava_available'] else '❌ Недоступен'}")
        except Exception as e:
            results['llava_error'] = str(e)
            logger.error(f"❌ Ошибка проверки LLaVA: {e}")
        
        return results
    
    def create_test_images(self) -> List[Path]:
        """Создание тестовых изображений для сравнения"""
        logger.info("🖼️ Создаем тестовые изображения...")
        
        test_images = []
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Создаем директорию для тестовых изображений
            test_dir = current_dir / "test_images"
            test_dir.mkdir(exist_ok=True)
            
            # Тестовое изображение 1: Простой текст
            img1 = Image.new('RGB', (800, 600), color='white')
            draw1 = ImageDraw.Draw(img1)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            text1 = """ТЕХНИЧЕСКИЙ РЕГЛАМЕНТ
Спутниковая связь VSAT

1. ОБЩИЕ ПОЛОЖЕНИЯ
1.1. Настоящий регламент определяет порядок работы с системой спутниковой связи VSAT.
1.2. Система предназначена для обеспечения связи в удаленных районах.

2. ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
2.1. Частота работы: 14/12 ГГц
2.2. Мощность передатчика: до 2 Вт
2.3. Диаметр антенны: 1.2-2.4 м

Дата: 2025-01-08
Версия: 1.0"""
            
            draw1.text((50, 50), text1, font=font, fill='black')
            img1_path = test_dir / "test_document_1.png"
            img1.save(img1_path)
            test_images.append(img1_path)
            
            # Тестовое изображение 2: Схема
            img2 = Image.new('RGB', (800, 600), color='white')
            draw2 = ImageDraw.Draw(img2)
            
            # Рисуем простую схему
            draw2.rectangle([100, 100, 300, 200], outline='black', width=2)
            draw2.text((150, 150), "VSAT Terminal", font=font, fill='black')
            
            draw2.rectangle([500, 100, 700, 200], outline='black', width=2)
            draw2.text((550, 150), "Satellite", font=font, fill='black')
            
            draw2.line([(300, 150), (500, 150)], fill='black', width=2)
            draw2.text((400, 120), "RF Link", font=font, fill='black')
            
            img2_path = test_dir / "test_diagram_1.png"
            img2.save(img2_path)
            test_images.append(img2_path)
            
            # Тестовое изображение 3: Таблица
            img3 = Image.new('RGB', (800, 600), color='white')
            draw3 = ImageDraw.Draw(img3)
            
            # Рисуем простую таблицу
            table_data = [
                ["Параметр", "Значение", "Единица"],
                ["Частота", "14/12", "ГГц"],
                ["Мощность", "2", "Вт"],
                ["Диаметр", "1.2-2.4", "м"]
            ]
            
            y_start = 100
            for i, row in enumerate(table_data):
                y = y_start + i * 40
                for j, cell in enumerate(row):
                    x = 100 + j * 200
                    draw3.rectangle([x, y, x+180, y+30], outline='black', width=1)
                    draw3.text((x+10, y+10), cell, font=font, fill='black')
            
            img3_path = test_dir / "test_table_1.png"
            img3.save(img3_path)
            test_images.append(img3_path)
            
            logger.info(f"✅ Создано {len(test_images)} тестовых изображений")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовых изображений: {e}")
            raise
        
        return test_images
    
    def test_image_analysis(self, image_path: Path) -> Dict[str, Any]:
        """Тестирование анализа одного изображения"""
        logger.info(f"🧪 Тестируем изображение: {image_path.name}")
        
        results = {
            'image_path': str(image_path),
            'image_name': image_path.name,
            'gemini_result': None,
            'llava_result': None,
            'comparison': {}
        }
        
        # Тестируем Gemini
        if self.vision_processor:
            try:
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
                
                logger.info(f"  Gemini: {'✅' if results['gemini_result']['success'] else '❌'} ({gemini_time:.2f}с)")
                
            except Exception as e:
                results['gemini_result'] = {
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                }
                logger.error(f"  ❌ Ошибка Gemini: {e}")
        
        # Тестируем LLaVA
        if self.llava_analyzer:
            try:
                start_time = time.time()
                llava_result = self.llava_analyzer.analyze_image(image_path)
                llava_time = time.time() - start_time
                
                results['llava_result'] = {
                    'success': llava_result.get('success', False),
                    'analysis': llava_result.get('analysis', ''),
                    'description': llava_result.get('description', ''),
                    'error': llava_result.get('error', ''),
                    'response_time': llava_time,
                    'model': llava_result.get('model_used', ''),
                    'provider': llava_result.get('provider', '')
                }
                
                logger.info(f"  LLaVA: {'✅' if results['llava_result']['success'] else '❌'} ({llava_time:.2f}с)")
                
            except Exception as e:
                results['llava_result'] = {
                    'success': False,
                    'error': str(e),
                    'response_time': 0
                }
                logger.error(f"  ❌ Ошибка LLaVA: {e}")
        
        # Сравнение результатов
        if results['gemini_result'] and results['llava_result']:
            results['comparison'] = self._compare_results(
                results['gemini_result'], 
                results['llava_result']
            )
        
        return results
    
    def _compare_results(self, gemini_result: Dict, llava_result: Dict) -> Dict[str, Any]:
        """Сравнение результатов Gemini и LLaVA"""
        comparison = {
            'both_successful': gemini_result['success'] and llava_result['success'],
            'gemini_faster': gemini_result['response_time'] < llava_result['response_time'],
            'speed_difference': abs(gemini_result['response_time'] - llava_result['response_time']),
            'quality_comparison': 'unknown'
        }
        
        # Простое сравнение качества по длине ответа
        if gemini_result['success'] and llava_result['success']:
            gemini_length = len(gemini_result['analysis'])
            llava_length = len(llava_result['analysis'])
            
            if gemini_length > llava_length * 1.2:
                comparison['quality_comparison'] = 'gemini_detailed'
            elif llava_length > gemini_length * 1.2:
                comparison['quality_comparison'] = 'llava_detailed'
            else:
                comparison['quality_comparison'] = 'similar'
        
        return comparison
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск полного тестирования"""
        logger.info("🚀 Запуск комплексного тестирования Gemini vs LLaVA...")
        
        # Проверяем доступность
        availability = self.check_availability()
        
        if not availability['gemini_available'] and not availability['llava_available']:
            return {
                'success': False,
                'error': 'Ни одна из систем не доступна',
                'availability': availability
            }
        
        # Создаем тестовые изображения
        test_images = self.create_test_images()
        
        # Тестируем каждое изображение
        test_results = []
        total_gemini_time = 0
        total_llava_time = 0
        successful_gemini = 0
        successful_llava = 0
        
        for image_path in test_images:
            result = self.test_image_analysis(image_path)
            test_results.append(result)
            
            # Подсчитываем статистику
            if result['gemini_result'] and result['gemini_result']['success']:
                total_gemini_time += result['gemini_result']['response_time']
                successful_gemini += 1
            
            if result['llava_result'] and result['llava_result']['success']:
                total_llava_time += result['llava_result']['response_time']
                successful_llava += 1
        
        # Анализ результатов
        analysis = self._analyze_test_results(test_results, availability)
        
        # Сохраняем результаты
        self._save_test_results(analysis, test_results)
        
        return analysis
    
    def _analyze_test_results(self, test_results: List[Dict], availability: Dict) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        logger.info("📊 Анализируем результаты...")
        
        total_tests = len(test_results)
        gemini_success_rate = 0
        llava_success_rate = 0
        avg_gemini_time = 0
        avg_llava_time = 0
        
        gemini_times = []
        llava_times = []
        
        for result in test_results:
            if result['gemini_result']:
                if result['gemini_result']['success']:
                    gemini_times.append(result['gemini_result']['response_time'])
            
            if result['llava_result']:
                if result['llava_result']['success']:
                    llava_times.append(result['llava_result']['response_time'])
        
        # Подсчитываем метрики
        if availability['gemini_available']:
            gemini_success_rate = len(gemini_times) / total_tests
            avg_gemini_time = sum(gemini_times) / len(gemini_times) if gemini_times else 0
        
        if availability['llava_available']:
            llava_success_rate = len(llava_times) / total_tests
            avg_llava_time = sum(llava_times) / len(llava_times) if llava_times else 0
        
        # Определяем рекомендации
        recommendations = []
        
        if availability['gemini_available'] and availability['llava_available']:
            if gemini_success_rate > llava_success_rate:
                recommendations.append("Gemini показывает лучшую надежность")
            elif llava_success_rate > gemini_success_rate:
                recommendations.append("LLaVA показывает лучшую надежность")
            
            if avg_gemini_time < avg_llava_time:
                recommendations.append("Gemini быстрее в среднем")
            elif avg_llava_time < avg_gemini_time:
                recommendations.append("LLaVA быстрее в среднем")
            
            if gemini_success_rate > 0.8 and llava_success_rate > 0.8:
                recommendations.append("Обе системы работают хорошо - можно использовать любую")
            elif gemini_success_rate > 0.8:
                recommendations.append("Рекомендуется использовать Gemini")
            elif llava_success_rate > 0.8:
                recommendations.append("Рекомендуется использовать LLaVA")
        elif availability['gemini_available']:
            recommendations.append("Доступен только Gemini - используйте его")
        elif availability['llava_available']:
            recommendations.append("Доступен только LLaVA - используйте его")
        else:
            recommendations.append("Ни одна система не доступна - проверьте настройки")
        
        return {
            'test_date': datetime.now().isoformat(),
            'total_tests': total_tests,
            'availability': availability,
            'gemini_metrics': {
                'success_rate': gemini_success_rate,
                'avg_response_time': avg_gemini_time,
                'total_successful': len(gemini_times)
            },
            'llava_metrics': {
                'success_rate': llava_success_rate,
                'avg_response_time': avg_llava_time,
                'total_successful': len(llava_times)
            },
            'recommendations': recommendations,
            'winner': self._determine_winner(gemini_success_rate, llava_success_rate, avg_gemini_time, avg_llava_time)
        }
    
    def _determine_winner(self, gemini_success: float, llava_success: float, 
                         gemini_time: float, llava_time: float) -> str:
        """Определение победителя на основе метрик"""
        if gemini_success > llava_success + 0.1:
            return "gemini"
        elif llava_success > gemini_success + 0.1:
            return "llava"
        elif gemini_time < llava_time * 0.8:
            return "gemini"
        elif llava_time < gemini_time * 0.8:
            return "llava"
        else:
            return "tie"
    
    def _save_test_results(self, analysis: Dict, test_results: List[Dict]):
        """Сохранение результатов тестирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"gemini_vs_llava_results_{timestamp}.json"
        
        full_results = {
            'analysis': analysis,
            'detailed_results': test_results
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
        print("📊 ОТЧЕТ О СРАВНЕНИИ GEMINI VS LLAVA")
        print("="*60)
        
        print(f"📅 Дата тестирования: {analysis['test_date']}")
        print(f"🧪 Всего тестов: {analysis['total_tests']}")
        
        # Статус доступности
        availability = analysis['availability']
        print(f"\n🔍 ДОСТУПНОСТЬ:")
        print(f"  Gemini: {'✅ Доступен' if availability['gemini_available'] else '❌ Недоступен'}")
        if availability['gemini_error']:
            print(f"    Ошибка: {availability['gemini_error']}")
        
        print(f"  LLaVA: {'✅ Доступен' if availability['llava_available'] else '❌ Недоступен'}")
        if availability['llava_error']:
            print(f"    Ошибка: {availability['llava_error']}")
        
        # Метрики Gemini
        if availability['gemini_available']:
            gemini_metrics = analysis['gemini_metrics']
            print(f"\n🤖 GEMINI МЕТРИКИ:")
            print(f"  Успешность: {gemini_metrics['success_rate']:.1%}")
            print(f"  Среднее время: {gemini_metrics['avg_response_time']:.2f}с")
            print(f"  Успешных тестов: {gemini_metrics['total_successful']}")
        
        # Метрики LLaVA
        if availability['llava_available']:
            llava_metrics = analysis['llava_metrics']
            print(f"\n🦙 LLAVA МЕТРИКИ:")
            print(f"  Успешность: {llava_metrics['success_rate']:.1%}")
            print(f"  Среднее время: {llava_metrics['avg_response_time']:.2f}с")
            print(f"  Успешных тестов: {llava_metrics['total_successful']}")
        
        # Победитель
        winner = analysis['winner']
        print(f"\n🏆 РЕЗУЛЬТАТ:")
        if winner == "gemini":
            print("  🥇 Победитель: Gemini")
        elif winner == "llava":
            print("  🥇 Победитель: LLaVA")
        else:
            print("  🤝 Ничья - обе системы показывают схожие результаты")
        
        # Рекомендации
        recommendations = analysis['recommendations']
        if recommendations:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("="*60)

def main():
    """Основная функция"""
    print("🤖 Тестирование Gemini vs LLaVA для обработки изображений")
    print("=" * 60)
    
    try:
        tester = GeminiVsLLaVATester()
        analysis = tester.run_comprehensive_test()
        tester.print_summary(analysis)
        
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()







