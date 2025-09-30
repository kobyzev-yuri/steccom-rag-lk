#!/usr/bin/env python3
"""
Демонстрация новых метрик производительности в протоколе тестирования KB
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


def demo_performance_metrics():
    """Демонстрация метрик производительности"""
    print("🚀 Демонстрация метрик производительности Knowledge Base")
    print("=" * 70)
    
    # Создание протокола
    protocol = KBTestProtocol()
    print("✅ Протокол создан")
    
    # Тестовые данные с разными характеристиками производительности
    test_scenarios = [
        {
            "name": "GPT-4o (быстрый и точный)",
            "model": "gpt-4o",
            "provider": "proxyapi",
            "response_time": 2.1,
            "accuracy": 0.9,
            "completeness": 0.85,
            "relevance": 0.9,
            "response_text": "Согласно регламенту SBD, исходящие электронные сообщения с абонентского терминала не должны превышать 340/1960 байт, а входящие сообщения - не более 270/1890 байт в зависимости от типа используемого абонентского терминала."
        },
        {
            "name": "Qwen (медленный но бесплатный)",
            "model": "qwen2.5:1.5b",
            "provider": "ollama",
            "response_time": 8.5,
            "accuracy": 0.7,
            "completeness": 0.6,
            "relevance": 0.75,
            "response_text": "В услуге SBD есть ограничения по размеру сообщений. Исходящие сообщения не должны превышать определенный размер, а входящие также имеют ограничения."
        },
        {
            "name": "GPT-3.5 (компромисс)",
            "model": "gpt-3.5-turbo",
            "provider": "proxyapi",
            "response_time": 1.8,
            "accuracy": 0.75,
            "completeness": 0.7,
            "relevance": 0.8,
            "response_text": "Для услуги SBD установлены ограничения по размеру сообщений: исходящие до 340/1960 байт, входящие до 270/1890 байт в зависимости от типа терминала."
        }
    ]
    
    print(f"\n📊 Тестирование {len(test_scenarios)} сценариев производительности...")
    
    # Используем первый вопрос из протокола
    question = LEGACY_SBD_TEST_QUESTIONS[0]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   ⏱️  Время ответа: {scenario['response_time']}с")
        print(f"   🎯 Точность: {scenario['accuracy']:.1%}")
        print(f"   📝 Полнота: {scenario['completeness']:.1%}")
        print(f"   🔗 Релевантность: {scenario['relevance']:.1%}")
        
        # Создание ответа модели
        model_response = ModelResponse(
            model_name=scenario["model"],
            provider=scenario["provider"],
            response_text=scenario["response_text"],
            response_time=scenario["response_time"],
            sources_found=1,
            sources_details=[{"source": "legacy_reglament_sbd.json", "relevance": 0.8}],
            timestamp=datetime.now().isoformat(),
            # Метрики токенов будут рассчитаны автоматически
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            tokens_per_second=0.0,
            cost_per_token=0.0,
            estimated_cost=0.0
        )
        
        # Оценка релевантности
        keywords_found = [kw for kw in question.expected_keywords if kw.lower() in scenario["response_text"].lower()]
        keywords_missing = [kw for kw in question.expected_keywords if kw.lower() not in scenario["response_text"].lower()]
        
        avg_score = (scenario["accuracy"] + scenario["completeness"] + scenario["relevance"]) / 3
        if avg_score >= 0.8:
            overall_quality = "excellent"
        elif avg_score >= 0.6:
            overall_quality = "good"
        elif avg_score >= 0.4:
            overall_quality = "fair"
        else:
            overall_quality = "poor"
        
        relevance_assessment = RelevanceAssessment(
            accuracy_score=scenario["accuracy"],
            completeness_score=scenario["completeness"],
            relevance_score=scenario["relevance"],
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            overall_quality=overall_quality,
            human_notes=f"Демонстрационный сценарий: {scenario['name']}",
            # Метрики эффективности будут рассчитаны автоматически
            efficiency_score=0.0,
            cost_effectiveness=0.0
        )
        
        # Добавление в протокол
        test_id = protocol.add_test_entry(question, model_response, relevance_assessment)
        print(f"   ✅ Тест {test_id} добавлен в протокол")
        
        # Показываем рассчитанные метрики
        print(f"   📈 Рассчитанные метрики:")
        print(f"      • Входные токены: {model_response.input_tokens}")
        print(f"      • Выходные токены: {model_response.output_tokens}")
        print(f"      • Всего токенов: {model_response.total_tokens}")
        print(f"      • Скорость генерации: {model_response.tokens_per_second:.1f} токенов/с")
        print(f"      • Стоимость: ${model_response.estimated_cost:.6f}")
        print(f"      • Эффективность: {relevance_assessment.efficiency_score:.4f}")
        print(f"      • Экономическая эффективность: {relevance_assessment.cost_effectiveness:.4f}")
    
    # Сохранение протокола
    print(f"\n💾 Сохранение протокола...")
    protocol_file = protocol.save_protocol()
    print(f"✅ Протокол сохранен: {protocol_file}")
    
    # Вывод сводки
    print(f"\n📊 Сводка тестирования производительности:")
    print(protocol.get_test_summary())
    
    # Экспорт детального отчета
    print(f"\n📋 Создание детального отчета...")
    report_file = protocol.export_detailed_report()
    print(f"✅ Детальный отчет создан: {report_file}")
    
    print(f"\n🎉 Демонстрация метрик производительности завершена!")
    print(f"📁 Файлы созданы:")
    print(f"   • Протокол: {protocol_file}")
    print(f"   • Отчет: {report_file}")
    
    # Анализ результатов
    print(f"\n🔍 Анализ результатов:")
    stats = protocol._calculate_summary_statistics()
    
    print(f"   🏆 Лучшая скорость генерации: {stats['average_tokens_per_second']:.1f} токенов/с")
    print(f"   💰 Общая стоимость тестирования: ${stats['total_estimated_cost']:.6f}")
    print(f"   ⚡ Средняя эффективность: {stats['average_efficiency_score']:.4f}")
    print(f"   💎 Средняя экономическая эффективность: {stats['average_cost_effectiveness']:.4f}")


if __name__ == "__main__":
    demo_performance_metrics()
