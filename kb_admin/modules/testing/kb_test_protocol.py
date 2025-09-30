#!/usr/bin/env python3
"""
Протокол тестирования Knowledge Base
Сохранение вопросов, контекста, ответов модели и оценок релевантности
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TestQuestion:
    """Структура тестового вопроса"""
    question_id: str
    question_text: str
    expected_keywords: List[str]
    category: str
    kb_source: str  # legacy_reglament_sbd.json
    difficulty_level: str  # easy, medium, hard
    expected_answer_type: str  # factual, procedural, technical


@dataclass
class ModelResponse:
    """Ответ модели на вопрос"""
    model_name: str
    provider: str
    response_text: str
    response_time: float
    sources_found: int
    sources_details: List[Dict[str, Any]]
    timestamp: str
    # Новые метрики производительности
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    tokens_per_second: float = 0.0
    cost_per_token: float = 0.0
    estimated_cost: float = 0.0


@dataclass
class RelevanceAssessment:
    """Оценка релевантности ответа"""
    accuracy_score: float  # 0.0 - 1.0
    completeness_score: float  # 0.0 - 1.0
    relevance_score: float  # 0.0 - 1.0
    keywords_found: List[str]
    keywords_missing: List[str]
    overall_quality: str  # excellent, good, fair, poor
    human_notes: Optional[str] = None
    # Дополнительные метрики производительности
    efficiency_score: float = 0.0  # 0.0 - 1.0 (соотношение качества к ресурсам)
    cost_effectiveness: float = 0.0  # 0.0 - 1.0 (качество на рубль)


@dataclass
class TestProtocolEntry:
    """Запись в протоколе тестирования"""
    test_id: str
    question: TestQuestion
    model_response: ModelResponse
    relevance_assessment: RelevanceAssessment
    test_timestamp: str
    test_environment: Dict[str, Any]


class KBTestProtocol:
    """Протокол тестирования Knowledge Base"""
    
    def __init__(self, protocol_file: str = None):
        self.protocol_file = protocol_file or f"/mnt/ai/cnn/steccom/tests/kb_test_protocol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.entries: List[TestProtocolEntry] = []
        self.test_environment = self._get_test_environment()
        
        # Стоимость токенов для разных моделей (примерные цены)
        self.token_costs = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # $ за 1K токенов
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "qwen2.5:1.5b": {"input": 0.0, "output": 0.0},  # Локальная модель
            "qwen2.5:7b": {"input": 0.0, "output": 0.0},   # Локальная модель
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Примерная оценка количества токенов в тексте"""
        # Простая эвристика: ~4 символа на токен для русского текста
        # Для более точной оценки можно использовать tiktoken
        return max(1, len(text) // 4)
    
    def calculate_token_metrics(self, 
                              question: str, 
                              answer: str, 
                              model_name: str, 
                              response_time: float) -> Dict[str, Any]:
        """Расчет метрик токенов и производительности"""
        input_tokens = self.estimate_tokens(question)
        output_tokens = self.estimate_tokens(answer)
        total_tokens = input_tokens + output_tokens
        
        # Скорость генерации токенов
        tokens_per_second = output_tokens / response_time if response_time > 0 else 0
        
        # Стоимость
        model_costs = self.token_costs.get(model_name, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "tokens_per_second": round(tokens_per_second, 2),
            "cost_per_token": round(total_cost / total_tokens, 6) if total_tokens > 0 else 0,
            "estimated_cost": round(total_cost, 6)
        }
    
    def calculate_efficiency_metrics(self, 
                                   accuracy: float, 
                                   completeness: float, 
                                   relevance: float,
                                   response_time: float,
                                   total_tokens: int,
                                   estimated_cost: float) -> Dict[str, float]:
        """Расчет метрик эффективности"""
        # Общая оценка качества
        quality_score = (accuracy + completeness + relevance) / 3
        
        # Эффективность (качество на единицу времени)
        efficiency_score = quality_score / response_time if response_time > 0 else 0
        
        # Экономическая эффективность (качество на рубль)
        cost_effectiveness = quality_score / estimated_cost if estimated_cost > 0 else float('inf')
        
        return {
            "efficiency_score": round(efficiency_score, 4),
            "cost_effectiveness": round(cost_effectiveness, 4)
        }
    
    def _get_test_environment(self) -> Dict[str, Any]:
        """Получение информации о среде тестирования"""
        return {
            "python_version": "3.x",
            "test_framework": "pytest",
            "rag_system": "MultiKBRAG",
            "knowledge_bases": ["legacy_reglament_sbd.json"],
            "test_date": datetime.now().isoformat(),
            "test_location": "/mnt/ai/cnn/steccom/tests/"
        }
    
    def add_test_entry(self, 
                      question: TestQuestion,
                      model_response: ModelResponse,
                      relevance_assessment: RelevanceAssessment) -> str:
        """Добавление записи в протокол с автоматическим расчетом метрик"""
        test_id = f"test_{len(self.entries) + 1:03d}_{datetime.now().strftime('%H%M%S')}"
        
        # Автоматический расчет метрик токенов, если они не заданы
        if model_response.input_tokens == 0 or model_response.output_tokens == 0:
            token_metrics = self.calculate_token_metrics(
                question.question_text,
                model_response.response_text,
                model_response.model_name,
                model_response.response_time
            )
            
            # Обновляем метрики в ответе модели
            model_response.input_tokens = token_metrics["input_tokens"]
            model_response.output_tokens = token_metrics["output_tokens"]
            model_response.total_tokens = token_metrics["total_tokens"]
            model_response.tokens_per_second = token_metrics["tokens_per_second"]
            model_response.cost_per_token = token_metrics["cost_per_token"]
            model_response.estimated_cost = token_metrics["estimated_cost"]
        
        # Автоматический расчет метрик эффективности
        if relevance_assessment.efficiency_score == 0.0 or relevance_assessment.cost_effectiveness == 0.0:
            efficiency_metrics = self.calculate_efficiency_metrics(
                relevance_assessment.accuracy_score,
                relevance_assessment.completeness_score,
                relevance_assessment.relevance_score,
                model_response.response_time,
                model_response.total_tokens,
                model_response.estimated_cost
            )
            
            relevance_assessment.efficiency_score = efficiency_metrics["efficiency_score"]
            relevance_assessment.cost_effectiveness = efficiency_metrics["cost_effectiveness"]
        
        entry = TestProtocolEntry(
            test_id=test_id,
            question=question,
            model_response=model_response,
            relevance_assessment=relevance_assessment,
            test_timestamp=datetime.now().isoformat(),
            test_environment=self.test_environment
        )
        
        self.entries.append(entry)
        return test_id
    
    def save_protocol(self) -> str:
        """Сохранение протокола в файл"""
        protocol_data = {
            "protocol_info": {
                "created_at": datetime.now().isoformat(),
                "total_tests": len(self.entries),
                "test_environment": self.test_environment
            },
            "test_entries": [asdict(entry) for entry in self.entries],
            "summary_statistics": self._calculate_summary_statistics()
        }
        
        with open(self.protocol_file, 'w', encoding='utf-8') as f:
            json.dump(protocol_data, f, ensure_ascii=False, indent=2)
        
        return self.protocol_file
    
    def _calculate_summary_statistics(self) -> Dict[str, Any]:
        """Расчет сводной статистики"""
        if not self.entries:
            return {}
        
        total_tests = len(self.entries)
        avg_accuracy = sum(entry.relevance_assessment.accuracy_score for entry in self.entries) / total_tests
        avg_completeness = sum(entry.relevance_assessment.completeness_score for entry in self.entries) / total_tests
        avg_relevance = sum(entry.relevance_assessment.relevance_score for entry in self.entries) / total_tests
        avg_response_time = sum(entry.model_response.response_time for entry in self.entries) / total_tests
        
        # Новые метрики производительности
        avg_tokens_per_second = sum(entry.model_response.tokens_per_second for entry in self.entries) / total_tests
        avg_total_tokens = sum(entry.model_response.total_tokens for entry in self.entries) / total_tests
        total_cost = sum(entry.model_response.estimated_cost for entry in self.entries)
        avg_efficiency = sum(entry.relevance_assessment.efficiency_score for entry in self.entries) / total_tests
        avg_cost_effectiveness = sum(entry.relevance_assessment.cost_effectiveness for entry in self.entries) / total_tests
        
        # Распределение по качеству
        quality_distribution = {}
        for entry in self.entries:
            quality = entry.relevance_assessment.overall_quality
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        # Распределение по категориям
        category_distribution = {}
        for entry in self.entries:
            category = entry.question.category
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        return {
            "total_tests": total_tests,
            "average_accuracy": round(avg_accuracy, 3),
            "average_completeness": round(avg_completeness, 3),
            "average_relevance": round(avg_relevance, 3),
            "average_response_time": round(avg_response_time, 2),
            "average_tokens_per_second": round(avg_tokens_per_second, 2),
            "average_total_tokens": round(avg_total_tokens, 0),
            "total_estimated_cost": round(total_cost, 6),
            "average_efficiency_score": round(avg_efficiency, 4),
            "average_cost_effectiveness": round(avg_cost_effectiveness, 4),
            "quality_distribution": quality_distribution,
            "category_distribution": category_distribution
        }
    
    def load_protocol(self, file_path: str) -> bool:
        """Загрузка протокола из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.protocol_file = file_path
            self.entries = []
            
            for entry_data in data.get("test_entries", []):
                entry = TestProtocolEntry(
                    test_id=entry_data["test_id"],
                    question=TestQuestion(**entry_data["question"]),
                    model_response=ModelResponse(**entry_data["model_response"]),
                    relevance_assessment=RelevanceAssessment(**entry_data["relevance_assessment"]),
                    test_timestamp=entry_data["test_timestamp"],
                    test_environment=entry_data["test_environment"]
                )
                self.entries.append(entry)
            
            return True
        except Exception as e:
            print(f"Ошибка загрузки протокола: {e}")
            return False
    
    def get_test_summary(self) -> str:
        """Получение текстового резюме тестов"""
        if not self.entries:
            return "Протокол пуст"
        
        stats = self._calculate_summary_statistics()
        
        summary = f"""
=== ПРОТОКОЛ ТЕСТИРОВАНИЯ KNOWLEDGE BASE ===
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Всего тестов: {stats['total_tests']}

КАЧЕСТВО ОТВЕТОВ:
• Точность: {stats['average_accuracy']:.1%}
• Полнота: {stats['average_completeness']:.1%}
• Релевантность: {stats['average_relevance']:.1%}

ПРОИЗВОДИТЕЛЬНОСТЬ:
• Время ответа: {stats['average_response_time']:.2f}с
• Скорость генерации: {stats['average_tokens_per_second']:.1f} токенов/с
• Среднее количество токенов: {stats['average_total_tokens']:.0f}

ЭКОНОМИЧЕСКАЯ ЭФФЕКТИВНОСТЬ:
• Общая стоимость: ${stats['total_estimated_cost']:.6f}
• Эффективность: {stats['average_efficiency_score']:.4f}
• Экономическая эффективность: {stats['average_cost_effectiveness']:.4f}

РАСПРЕДЕЛЕНИЕ ПО КАЧЕСТВУ:
"""
        for quality, count in stats['quality_distribution'].items():
            percentage = (count / stats['total_tests']) * 100
            summary += f"• {quality}: {count} ({percentage:.1f}%)\n"
        
        summary += "\nРАСПРЕДЕЛЕНИЕ ПО КАТЕГОРИЯМ:\n"
        for category, count in stats['category_distribution'].items():
            percentage = (count / stats['total_tests']) * 100
            summary += f"• {category}: {count} ({percentage:.1f}%)\n"
        
        return summary
    
    def export_detailed_report(self, output_file: str = None) -> str:
        """Экспорт детального отчета"""
        if output_file is None:
            output_file = f"/mnt/ai/cnn/steccom/tests/kb_detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Детальный отчет тестирования Knowledge Base\n\n")
            f.write(f"**Дата создания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Сводка
            stats = self._calculate_summary_statistics()
            f.write("## Сводная статистика\n\n")
            f.write(f"- **Всего тестов:** {stats['total_tests']}\n")
            f.write(f"- **Средняя точность:** {stats['average_accuracy']:.1%}\n")
            f.write(f"- **Средняя полнота:** {stats['average_completeness']:.1%}\n")
            f.write(f"- **Средняя релевантность:** {stats['average_relevance']:.1%}\n")
            f.write(f"- **Среднее время ответа:** {stats['average_response_time']:.2f}с\n")
            f.write(f"- **Скорость генерации:** {stats['average_tokens_per_second']:.1f} токенов/с\n")
            f.write(f"- **Среднее количество токенов:** {stats['average_total_tokens']:.0f}\n")
            f.write(f"- **Общая стоимость:** ${stats['total_estimated_cost']:.6f}\n")
            f.write(f"- **Эффективность:** {stats['average_efficiency_score']:.4f}\n")
            f.write(f"- **Экономическая эффективность:** {stats['average_cost_effectiveness']:.4f}\n\n")
            
            # Детальные результаты
            f.write("## Детальные результаты тестов\n\n")
            for i, entry in enumerate(self.entries, 1):
                f.write(f"### Тест {i}: {entry.test_id}\n\n")
                f.write(f"**Вопрос:** {entry.question.question_text}\n\n")
                f.write(f"**Категория:** {entry.question.category}\n")
                f.write(f"**Источник KB:** {entry.question.kb_source}\n")
                f.write(f"**Модель:** {entry.model_response.model_name} ({entry.model_response.provider})\n\n")
                f.write(f"**Ответ модели:**\n{entry.model_response.response_text}\n\n")
                f.write(f"**Оценки качества:**\n")
                f.write(f"- Точность: {entry.relevance_assessment.accuracy_score:.1%}\n")
                f.write(f"- Полнота: {entry.relevance_assessment.completeness_score:.1%}\n")
                f.write(f"- Релевантность: {entry.relevance_assessment.relevance_score:.1%}\n")
                f.write(f"- Общее качество: {entry.relevance_assessment.overall_quality}\n\n")
                
                f.write(f"**Метрики производительности:**\n")
                f.write(f"- Время ответа: {entry.model_response.response_time:.2f}с\n")
                f.write(f"- Входные токены: {entry.model_response.input_tokens}\n")
                f.write(f"- Выходные токены: {entry.model_response.output_tokens}\n")
                f.write(f"- Всего токенов: {entry.model_response.total_tokens}\n")
                f.write(f"- Скорость генерации: {entry.model_response.tokens_per_second:.1f} токенов/с\n")
                f.write(f"- Стоимость: ${entry.model_response.estimated_cost:.6f}\n")
                f.write(f"- Эффективность: {entry.relevance_assessment.efficiency_score:.4f}\n")
                f.write(f"- Экономическая эффективность: {entry.relevance_assessment.cost_effectiveness:.4f}\n\n")
                
                if entry.relevance_assessment.keywords_found:
                    f.write(f"**Найденные ключевые слова:** {', '.join(entry.relevance_assessment.keywords_found)}\n\n")
                
                if entry.relevance_assessment.keywords_missing:
                    f.write(f"**Отсутствующие ключевые слова:** {', '.join(entry.relevance_assessment.keywords_missing)}\n\n")
                
                if entry.relevance_assessment.human_notes:
                    f.write(f"**Примечания:** {entry.relevance_assessment.human_notes}\n\n")
                
                f.write("---\n\n")
        
        return output_file


# Предопределенные тестовые вопросы для legacy_reglament_sbd.json
LEGACY_SBD_TEST_QUESTIONS = [
    TestQuestion(
        question_id="sbd_001",
        question_text="Какие ограничения по размеру сообщений действуют для абонентских терминалов в услуге SBD?",
        expected_keywords=["340/1960 байт", "270/1890 байт", "зависимости от типа терминала", "абонентский терминал"],
        category="technical_limits",
        kb_source="legacy_reglament_sbd.json",
        difficulty_level="medium",
        expected_answer_type="factual"
    ),
    TestQuestion(
        question_id="sbd_002", 
        question_text="Какие правила действуют при деактивации абонентского терминала в течение месяца?",
        expected_keywords=["не чаще чем 1 раз в месяц", "не в один и тот же день", "одноразовая плата", "начиная со второй деактивации", "день деактивации - неактивный"],
        category="deactivation_rules",
        kb_source="legacy_reglament_sbd.json",
        difficulty_level="hard",
        expected_answer_type="procedural"
    ),
    TestQuestion(
        question_id="sbd_003",
        question_text="Снимается ли плата за день, если услуга деактивирована?",
        expected_keywords=["другая абонентская плата", "пропорционально доле неактивных дней", "финансовый период", "день деактивации - неактивный", "время деактивированной услуги"],
        category="billing_rules",
        kb_source="legacy_reglament_sbd.json", 
        difficulty_level="hard",
        expected_answer_type="factual"
    )
]


def create_test_protocol() -> KBTestProtocol:
    """Создание нового протокола тестирования"""
    return KBTestProtocol()


if __name__ == "__main__":
    # Пример использования
    protocol = create_test_protocol()
    
    # Добавление тестового вопроса
    question = LEGACY_SBD_TEST_QUESTIONS[0]
    
    # Симуляция ответа модели
    model_response = ModelResponse(
        model_name="gpt-4o",
        provider="proxyapi",
        response_text="Согласно регламенту SBD, исходящие электронные сообщения с абонентского терминала не должны превышать 340/1960 байт, а входящие сообщения - не более 270/1890 байт в зависимости от типа используемого абонентского терминала.",
        response_time=2.5,
        sources_found=1,
        sources_details=[{"source": "legacy_reglament_sbd.json", "relevance": 0.9}],
        timestamp=datetime.now().isoformat()
    )
    
    # Оценка релевантности
    relevance_assessment = RelevanceAssessment(
        accuracy_score=0.9,
        completeness_score=0.8,
        relevance_score=0.9,
        keywords_found=["340/1960 байт", "270/1890 байт", "зависимости от типа терминала", "абонентский терминал"],
        keywords_missing=[],
        overall_quality="excellent",
        human_notes="Отличный ответ, содержит все ключевые технические детали"
    )
    
    # Добавление в протокол
    test_id = protocol.add_test_entry(question, model_response, relevance_assessment)
    print(f"Добавлен тест: {test_id}")
    
    # Сохранение протокола
    protocol_file = protocol.save_protocol()
    print(f"Протокол сохранен: {protocol_file}")
    
    # Вывод сводки
    print(protocol.get_test_summary())
