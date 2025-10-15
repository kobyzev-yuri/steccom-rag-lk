#!/usr/bin/env python3
"""
Быстрый тест анализа изображений с оптимизацией
"""

import sys
import os
from pathlib import Path
from PIL import Image
import time

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def optimize_image(image_path: Path, max_size: int = 1024) -> Path:
    """Оптимизация изображения для быстрого анализа"""
    try:
        with Image.open(image_path) as img:
            # Изменяем размер если нужно
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Сохраняем оптимизированную версию
            optimized_path = image_path.parent / f"optimized_{image_path.name}"
            img.save(optimized_path, "PNG", optimize=True)
            return optimized_path
    except Exception as e:
        print(f"Ошибка оптимизации: {e}")
        return image_path

def test_llava_analysis(image_path: Path):
    """Тест LLaVA анализа"""
    print(f"🦙 Тестируем LLaVA на {image_path.name}")
    
    try:
        from modules.core.llava_analyzer import LLaVAAnalyzer
        analyzer = LLaVAAnalyzer()
        analyzer.set_model("llava-phi3:latest")
        
        if not analyzer.is_available():
            print("❌ LLaVA недоступен")
            return None
        
        start_time = time.time()
        result = analyzer.analyze_image(image_path, "Опиши это изображение подробно на русском языке")
        analysis_time = time.time() - start_time
        
        if result.get('success'):
            print(f"✅ LLaVA успешно проанализировал за {analysis_time:.2f}с")
            print(f"📝 Анализ: {result.get('analysis', '')[:200]}...")
            return {
                'success': True,
                'time': analysis_time,
                'analysis': result.get('analysis', ''),
                'model': result.get('model_used', '')
            }
        else:
            print(f"❌ LLaVA ошибка: {result.get('error', '')}")
            return {'success': False, 'error': result.get('error', '')}
            
    except Exception as e:
        print(f"❌ Ошибка LLaVA: {e}")
        return {'success': False, 'error': str(e)}

def test_gemini_analysis(image_path: Path):
    """Тест Gemini анализа"""
    print(f"🤖 Тестируем Gemini на {image_path.name}")
    
    try:
        from modules.documents.vision_processor import VisionProcessor
        processor = VisionProcessor()
        
        start_time = time.time()
        result = processor.analyze_image_with_gemini(image_path)
        analysis_time = time.time() - start_time
        
        if result.get('success'):
            print(f"✅ Gemini успешно проанализировал за {analysis_time:.2f}с")
            print(f"📝 Анализ: {result.get('analysis', '')[:200]}...")
            return {
                'success': True,
                'time': analysis_time,
                'analysis': result.get('analysis', ''),
                'model': result.get('model', '')
            }
        else:
            print(f"❌ Gemini ошибка: {result.get('error', '')}")
            return {'success': False, 'error': result.get('error', '')}
            
    except Exception as e:
        print(f"❌ Ошибка Gemini: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Основная функция"""
    print("🚀 БЫСТРЫЙ ТЕСТ АНАЛИЗА ИЗОБРАЖЕНИЙ")
    print("=" * 50)
    
    # Берем первое изображение
    image_path = Path("extracted_images/Access-SkyEdge-II--170414-FINAL/page_1_img_2.png")
    
    if not image_path.exists():
        print(f"❌ Изображение не найдено: {image_path}")
        return
    
    print(f"📷 Тестируем: {image_path.name} ({image_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # Оптимизируем изображение
    print("🔧 Оптимизируем изображение...")
    optimized_path = optimize_image(image_path, max_size=1024)
    print(f"✅ Оптимизировано: {optimized_path.name} ({optimized_path.stat().st_size / 1024:.1f} KB)")
    
    # Тестируем LLaVA
    print("\n" + "="*30)
    llava_result = test_llava_analysis(optimized_path)
    
    # Тестируем Gemini
    print("\n" + "="*30)
    gemini_result = test_gemini_analysis(optimized_path)
    
    # Сравнение результатов
    print("\n" + "="*50)
    print("📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*50)
    
    if llava_result and gemini_result:
        if llava_result.get('success') and gemini_result.get('success'):
            print("✅ Обе системы работают!")
            print(f"🦙 LLaVA: {llava_result['time']:.2f}с")
            print(f"🤖 Gemini: {gemini_result['time']:.2f}с")
            
            if llava_result['time'] < gemini_result['time']:
                print("🏆 LLaVA быстрее")
            else:
                print("🏆 Gemini быстрее")
                
            # Сравниваем качество анализа
            llava_len = len(llava_result.get('analysis', ''))
            gemini_len = len(gemini_result.get('analysis', ''))
            print(f"📝 LLaVA анализ: {llava_len} символов")
            print(f"📝 Gemini анализ: {gemini_len} символов")
            
        elif llava_result.get('success'):
            print("✅ Только LLaVA работает")
        elif gemini_result.get('success'):
            print("✅ Только Gemini работает")
        else:
            print("❌ Ни одна система не работает")
    else:
        print("❌ Ошибка тестирования")

if __name__ == "__main__":
    main()







