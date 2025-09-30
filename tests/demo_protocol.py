#!/usr/bin/env python3
"""
Демонстрация работы протокола тестирования Knowledge Base
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kb_test_protocol import (
    KBTestProtocol, 
    TestQuestion, 
    ModelResponse, 
    RelevanceAssessment,
    LEGACY_SBD_TEST_QUESTIONS
)
from datetime import datetime


def demo_protocol_usage():
    """Демонстрация использования протокола"""
    print("🚀 Демонстрация протокола тестирования Knowledge Base")
    print("=" * 60)
    
    # Создание протокола
    protocol = KBTestProtocol()
    print("✅ Протокол создан")
    
    # Добавление тестовых записей
    print("\n📝 Добавление тестовых записей...")
    
    for i, question in enumerate(LEGACY_SBD_TEST_QUESTIONS, 1):
        print(f"\n{i}. Тестирование вопроса: {question.question_text[:50]}...")
        
        # Симуляция ответа модели GPT-4o
        gpt4o_response = ModelResponse(
            model_name="gpt-4o",
            provider="proxyapi",
            response_text=f"Ответ GPT-4o на вопрос о {question.category}",
            response_time=2.5 + i * 0.5,
            sources_found=1,
            sources_details=[{"source": "legacy_reglament_sbd.json", "relevance": 0.9}],
            timestamp=datetime.now().isoformat(),
            # Метрики токенов будут рассчитаны автоматически
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            tokens_per_second=0.0,
            cost_per_token=0.0,
            estimated_cost=0.0
        )
        
        # Оценка релевантности для GPT-4o
        gpt4o_assessment = RelevanceAssessment(
            accuracy_score=0.8 + i * 0.05,
            completeness_score=0.7 + i * 0.05,
            relevance_score=0.9 - i * 0.05,
            keywords_found=question.expected_keywords[:2],  # Симуляция найденных ключевых слов
            keywords_missing=question.expected_keywords[2:],  # Симуляция отсутствующих
            overall_quality="good" if i % 2 == 0 else "excellent",
            human_notes=f"Автоматическая оценка для GPT-4o, вопрос {i}"
        )
        
        # Добавление в протокол
        test_id = protocol.add_test_entry(question, gpt4o_response, gpt4o_assessment)
        print(f"   ✅ Добавлен тест: {test_id}")
        
        # Симуляция ответа модели Qwen
        qwen_response = ModelResponse(
            model_name="qwen2.5:1.5b",
            provider="ollama",
            response_text=f"Ответ Qwen на вопрос о {question.category}",
            response_time=1.2 + i * 0.3,
            sources_found=1,
            sources_details=[{"source": "legacy_reglament_sbd.json", "relevance": 0.7}],
            timestamp=datetime.now().isoformat(),
            # Метрики токенов будут рассчитаны автоматически
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            tokens_per_second=0.0,
            cost_per_token=0.0,
            estimated_cost=0.0
        )
        
        # Оценка релевантности для Qwen
        qwen_assessment = RelevanceAssessment(
            accuracy_score=0.6 + i * 0.05,
            completeness_score=0.5 + i * 0.05,
            relevance_score=0.7 - i * 0.05,
            keywords_found=question.expected_keywords[:1],  # Qwen находит меньше ключевых слов
            keywords_missing=question.expected_keywords[1:],
            overall_quality="fair" if i % 2 == 0 else "good",
            human_notes=f"Автоматическая оценка для Qwen, вопрос {i}"
        )
        
        # Добавление в протокол
        test_id = protocol.add_test_entry(question, qwen_response, qwen_assessment)
        print(f"   ✅ Добавлен тест: {test_id}")
    
    # Сохранение протокола
    print(f"\n💾 Сохранение протокола...")
    protocol_file = protocol.save_protocol()
    print(f"✅ Протокол сохранен: {protocol_file}")
    
    # Вывод сводки
    print(f"\n📊 Сводка тестирования:")
    print(protocol.get_test_summary())
    
    # Экспорт детального отчета
    print(f"\n📋 Создание детального отчета...")
    report_file = protocol.export_detailed_report()
    print(f"✅ Детальный отчет создан: {report_file}")
    
    print(f"\n🎉 Демонстрация завершена!")
    print(f"📁 Файлы созданы:")
    print(f"   • Протокол: {protocol_file}")
    print(f"   • Отчет: {report_file}")


if __name__ == "__main__":
    demo_protocol_usage()
