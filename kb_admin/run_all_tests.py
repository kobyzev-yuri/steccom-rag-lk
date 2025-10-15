#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов
- Тестирование моделей (qwen2.5-coder, qwen3:8b, llama3)
- Сравнение Gemini vs LLaVA
- Восстановление KB с Gemini
"""

import sys
import os
import subprocess
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path: Path, description: str):
    """Запуск скрипта с обработкой ошибок"""
    print(f"\n🚀 {description}")
    print("=" * 50)
    
    try:
        if not script_path.exists():
            print(f"❌ Скрипт не найден: {script_path}")
            return False
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - УСПЕШНО")
            if result.stdout:
                print("📄 Вывод:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - ОШИБКА")
            if result.stderr:
                print("📄 Ошибки:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - ТАЙМАУТ (5 минут)")
        return False
    except Exception as e:
        print(f"❌ {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def main():
    """Основная функция запуска тестов"""
    print("🧪 ЗАПУСК ВСЕХ ТЕСТОВ KB ADMIN")
    print("=" * 60)
    
    current_dir = Path(__file__).parent
    
    # Список тестов для запуска
    tests = [
        {
            'script': current_dir / 'test_models_comparison.py',
            'description': 'Тестирование моделей (qwen2.5-coder, qwen3:8b, llama3)',
            'required': True
        },
        {
            'script': current_dir / 'test_gemini_vs_llava.py',
            'description': 'Сравнение Gemini vs LLaVA для обработки изображений',
            'required': False
        },
        {
            'script': current_dir / 'restore_gemini_kb_creation.py',
            'description': 'Восстановление создания KB с Gemini',
            'required': False
        }
    ]
    
    results = {}
    
    for test in tests:
        success = run_script(test['script'], test['description'])
        results[test['description']] = success
        
        if not success and test['required']:
            print(f"\n⚠️ КРИТИЧЕСКИЙ ТЕСТ ПРОВАЛЕН: {test['description']}")
            print("Продолжаем с остальными тестами...")
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    
    total_tests = len(tests)
    successful_tests = sum(1 for success in results.values() if success)
    
    print(f"Всего тестов: {total_tests}")
    print(f"Успешных: {successful_tests}")
    print(f"Проваленных: {total_tests - successful_tests}")
    
    print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for description, success in results.items():
        status = "✅ УСПЕШНО" if success else "❌ ПРОВАЛЕНО"
        print(f"  {status}: {description}")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    
    if results.get('Тестирование моделей (qwen2.5-coder, qwen3:8b, llama3)', False):
        print("  • Модели протестированы - проверьте результаты в model_test_results_*.json")
    else:
        print("  • ⚠️ Тестирование моделей не прошло - проверьте Ollama и ProxyAPI")
    
    if results.get('Сравнение Gemini vs LLaVA для обработки изображений', False):
        print("  • Сравнение Gemini vs LLaVA завершено - проверьте gemini_vs_llava_results_*.json")
    else:
        print("  • ⚠️ Сравнение Gemini vs LLaVA не прошло - проверьте настройки")
    
    if results.get('Восстановление создания KB с Gemini', False):
        print("  • KB с Gemini восстановлены - можно использовать для создания баз знаний")
    else:
        print("  • ⚠️ Восстановление KB с Gemini не прошло - проверьте конфигурацию")
    
    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("  1. Проверьте логи тестирования")
    print("  2. Изучите JSON файлы с результатами")
    print("  3. Настройте лучшие модели на основе результатов")
    print("  4. Запустите KB Admin для проверки работы")
    
    print("\n" + "="*60)
    
    # Возвращаем код выхода
    if successful_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return 0
    elif successful_tests > 0:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ - ПРОВЕРЬТЕ НАСТРОЙКИ")
        return 1
    else:
        print("❌ ВСЕ ТЕСТЫ ПРОВАЛЕНЫ - ТРЕБУЕТСЯ НАСТРОЙКА СИСТЕМЫ")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)







