#!/usr/bin/env python3
"""
Comprehensive Knowledge Base Effectiveness Tests
Тесты эффективности базы знаний для системы СТЭККОМ

Этот модуль содержит тесты для оценки:
- Точности ответов KB
- Полноты покрытия тем
- Релевантности результатов поиска
- Производительности системы
- Качества структурированных ответов
"""

import os
import sys
import time
import pytest
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.rag.multi_kb_rag import MultiKBRAG
from kb_test_protocol import KBTestProtocol, TestQuestion, ModelResponse, RelevanceAssessment, LEGACY_SBD_TEST_QUESTIONS


@dataclass
class KBTestResult:
    """Результат теста KB"""
    question: str
    expected_keywords: List[str]
    actual_answer: str
    response_time: float
    sources_found: int
    accuracy_score: float
    completeness_score: float
    relevance_score: float
    model_used: str
    timestamp: str


class KBEffectivenessTester:
    """Тестер эффективности Knowledge Base"""
    
    def __init__(self):
        self.rag = MultiKBRAG()
        self.test_results: List[KBTestResult] = []
        self.protocol = KBTestProtocol()
        
        # Стандартные тестовые вопросы с ожидаемыми ключевыми словами
        self.test_questions = {
            "billing": [
                {
                    "question": "Как рассчитывается включенный трафик при подключении в середине месяца?",
                    "expected_keywords": ["пропорционально", "активных дней", "финансовый период", "расчет"],
                    "category": "billing_calculation"
                },
                {
                    "question": "Какие правила действуют при деактивации терминала в течение месяца?",
                    "expected_keywords": ["деактивац", "месяц", "плата", "правила"],
                    "category": "deactivation_rules"
                },
                {
                    "question": "Как тарифицируется трафик электронных сообщений и когда он попадает в счет?",
                    "expected_keywords": ["тарифицир", "следующий день", "финансовый период", "электронные сообщения"],
                    "category": "traffic_tarification"
                },
                {
                    "question": "Сколько байт в одном килобайте согласно тарифам?",
                    "expected_keywords": ["1000", "байт", "килобайт", "тариф"],
                    "category": "data_units"
                }
            ],
            "ui_guide": [
                {
                    "question": "Какие возможности есть в личном кабинете?",
                    "expected_keywords": ["аналитика", "трафик", "договоры", "мониторинг", "устройств"],
                    "category": "ui_capabilities"
                },
                {
                    "question": "Как работать с отчетами в системе?",
                    "expected_keywords": ["отчеты", "список", "показать", "csv", "скачать"],
                    "category": "reports_usage"
                },
                {
                    "question": "Что такое SQL-агент и как им пользоваться?",
                    "expected_keywords": ["sql", "агент", "генерация", "запрос", "вопрос"],
                    "category": "sql_agent"
                }
            ],
            "technical": [
                {
                    "question": "Какие таблицы используются в базе данных?",
                    "expected_keywords": ["таблицы", "users", "devices", "sessions", "billing_records"],
                    "category": "database_structure"
                },
                {
                    "question": "Как работает умный помощник RAG?",
                    "expected_keywords": ["rag", "помощник", "документация", "kb", "отвечает"],
                    "category": "rag_system"
                }
            ]
        }
    
    def run_comprehensive_effectiveness_test(self, model_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Запуск комплексного теста эффективности KB"""
        if model_configs is None:
            model_configs = [
                {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0},
                {"provider": "ollama", "model": "qwen2.5:1.5b", "temperature": 0.0}
            ]
        
        print("🚀 Запуск комплексного теста эффективности Knowledge Base...")
        print(f"📊 Тестируем {len(model_configs)} моделей")
        print(f"📝 Всего вопросов: {sum(len(questions) for questions in self.test_questions.values())}")
        
        all_results = {}
        
        for config in model_configs:
            print(f"\n🤖 Тестирование модели: {config['model']} ({config['provider']})")
            
            # Настройка модели
            self.rag.set_chat_backend(
                provider=config["provider"],
                model=config["model"],
                temperature=config["temperature"]
            )
            
            model_results = self._test_model_effectiveness(config)
            all_results[f"{config['provider']}_{config['model']}"] = model_results
        
        # Анализ результатов
        analysis = self._analyze_results(all_results)
        
        # Сохранение результатов
        self._save_test_results(all_results, analysis)
        
        return {
            "model_results": all_results,
            "analysis": analysis,
            "summary": self._generate_summary(analysis)
        }
    
    def run_protocol_test(self, model_configs: List[Dict[str, Any]] = None) -> str:
        """Запуск тестирования с сохранением в протокол"""
        if model_configs is None:
            model_configs = [
                {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0},
                {"provider": "ollama", "model": "qwen2.5:1.5b", "temperature": 0.0}
            ]
        
        print("📋 Запуск тестирования с протоколированием...")
        
        for config in model_configs:
            print(f"\n🤖 Тестирование модели: {config['model']} ({config['provider']})")
            
            # Настройка модели
            self.rag.set_chat_backend(
                provider=config["provider"],
                model=config["model"],
                temperature=config["temperature"]
            )
            
            # Тестирование каждого вопроса из протокола
            for question in LEGACY_SBD_TEST_QUESTIONS:
                print(f"  ❓ {question.question_text[:50]}...")
                
                # Выполнение теста
                start_time = time.time()
                try:
                    result = self.rag.ask_question(question.question_text)
                    response_time = time.time() - start_time
                    
                    answer = result.get("answer", "")
                    sources = result.get("sources", [])
                    
                    # Создание ответа модели
                    model_response = ModelResponse(
                        model_name=config["model"],
                        provider=config["provider"],
                        response_text=answer,
                        response_time=response_time,
                        sources_found=len(sources),
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
                    accuracy_score = self._calculate_accuracy_score(answer, question.expected_keywords)
                    completeness_score = self._calculate_completeness_score(answer, question.expected_keywords)
                    relevance_score = self._calculate_relevance_score(answer, question.question_text)
                    
                    keywords_found = [kw for kw in question.expected_keywords if kw.lower() in answer.lower()]
                    keywords_missing = [kw for kw in question.expected_keywords if kw.lower() not in answer.lower()]
                    
                    # Определение общего качества
                    avg_score = (accuracy_score + completeness_score + relevance_score) / 3
                    if avg_score >= 0.8:
                        overall_quality = "excellent"
                    elif avg_score >= 0.6:
                        overall_quality = "good"
                    elif avg_score >= 0.4:
                        overall_quality = "fair"
                    else:
                        overall_quality = "poor"
                    
                    relevance_assessment = RelevanceAssessment(
                        accuracy_score=accuracy_score,
                        completeness_score=completeness_score,
                        relevance_score=relevance_score,
                        keywords_found=keywords_found,
                        keywords_missing=keywords_missing,
                        overall_quality=overall_quality,
                        human_notes=f"Автоматическая оценка для {config['model']}",
                        # Метрики эффективности будут рассчитаны автоматически
                        efficiency_score=0.0,
                        cost_effectiveness=0.0
                    )
                    
                    # Добавление в протокол
                    test_id = self.protocol.add_test_entry(question, model_response, relevance_assessment)
                    print(f"    ✅ Тест {test_id} добавлен в протокол")
                    
                except Exception as e:
                    print(f"    ❌ Ошибка: {e}")
                    # Добавляем запись об ошибке
                    error_response = ModelResponse(
                        model_name=config["model"],
                        provider=config["provider"],
                        response_text=f"Ошибка: {str(e)}",
                        response_time=time.time() - start_time,
                        sources_found=0,
                        sources_details=[],
                        timestamp=datetime.now().isoformat(),
                        # Метрики токенов будут рассчитаны автоматически
                        input_tokens=0,
                        output_tokens=0,
                        total_tokens=0,
                        tokens_per_second=0.0,
                        cost_per_token=0.0,
                        estimated_cost=0.0
                    )
                    
                    error_assessment = RelevanceAssessment(
                        accuracy_score=0.0,
                        completeness_score=0.0,
                        relevance_score=0.0,
                        keywords_found=[],
                        keywords_missing=question.expected_keywords,
                        overall_quality="poor",
                        human_notes=f"Ошибка выполнения: {str(e)}",
                        # Метрики эффективности будут рассчитаны автоматически
                        efficiency_score=0.0,
                        cost_effectiveness=0.0
                    )
                    
                    self.protocol.add_test_entry(question, error_response, error_assessment)
        
        # Сохранение протокола
        protocol_file = self.protocol.save_protocol()
        print(f"\n💾 Протокол сохранен: {protocol_file}")
        
        # Вывод сводки
        print(self.protocol.get_test_summary())
        
        # Экспорт детального отчета
        report_file = self.protocol.export_detailed_report()
        print(f"📊 Детальный отчет: {report_file}")
        
        return protocol_file
    
    def _test_model_effectiveness(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Тестирование эффективности конкретной модели"""
        model_results = {
            "config": config,
            "category_results": {},
            "overall_metrics": {},
            "test_results": []
        }
        
        total_questions = 0
        total_accuracy = 0
        total_completeness = 0
        total_relevance = 0
        total_response_time = 0
        
        for category, questions in self.test_questions.items():
            print(f"  📂 Тестирование категории: {category}")
            category_results = []
            
            for question_data in questions:
                question = question_data["question"]
                expected_keywords = question_data["expected_keywords"]
                question_category = question_data["category"]
                
                print(f"    ❓ {question[:50]}...")
                
                # Выполнение теста
                result = self._test_single_question(
                    question, expected_keywords, config["model"]
                )
                
                category_results.append(result)
                model_results["test_results"].append(result)
                
                # Накопление метрик
                total_questions += 1
                total_accuracy += result.accuracy_score
                total_completeness += result.completeness_score
                total_relevance += result.relevance_score
                total_response_time += result.response_time
        
        # Расчет общих метрик
        model_results["overall_metrics"] = {
            "total_questions": total_questions,
            "average_accuracy": total_accuracy / total_questions if total_questions > 0 else 0,
            "average_completeness": total_completeness / total_questions if total_questions > 0 else 0,
            "average_relevance": total_relevance / total_questions if total_questions > 0 else 0,
            "average_response_time": total_response_time / total_questions if total_questions > 0 else 0,
            "total_response_time": total_response_time
        }
        
        return model_results
    
    def _test_single_question(self, question: str, expected_keywords: List[str], model_name: str) -> KBTestResult:
        """Тестирование одного вопроса"""
        start_time = time.time()
        
        try:
            result = self.rag.ask_question(question)
            response_time = time.time() - start_time
            
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # Оценка качества ответа
            accuracy_score = self._calculate_accuracy_score(answer, expected_keywords)
            completeness_score = self._calculate_completeness_score(answer, expected_keywords)
            relevance_score = self._calculate_relevance_score(answer, question)
            
            return KBTestResult(
                question=question,
                expected_keywords=expected_keywords,
                actual_answer=answer,
                response_time=response_time,
                sources_found=len(sources),
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                relevance_score=relevance_score,
                model_used=model_name,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"    ❌ Ошибка при тестировании: {e}")
            return KBTestResult(
                question=question,
                expected_keywords=expected_keywords,
                actual_answer=f"Ошибка: {str(e)}",
                response_time=time.time() - start_time,
                sources_found=0,
                accuracy_score=0.0,
                completeness_score=0.0,
                relevance_score=0.0,
                model_used=model_name,
                timestamp=datetime.now().isoformat()
            )
    
    def _calculate_accuracy_score(self, answer: str, expected_keywords: List[str]) -> float:
        """Расчет оценки точности (наличие ключевых слов)"""
        if not answer:
            return 0.0
        
        answer_lower = answer.lower()
        found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in answer_lower)
        return found_keywords / len(expected_keywords)
    
    def _calculate_completeness_score(self, answer: str, expected_keywords: List[str]) -> float:
        """Расчет оценки полноты ответа"""
        if not answer:
            return 0.0
        
        # Базовая оценка на основе длины ответа
        length_score = min(len(answer) / 200, 1.0)  # Нормализация к 200 символам
        
        # Бонус за наличие ключевых слов
        keyword_score = self._calculate_accuracy_score(answer, expected_keywords)
        
        # Комбинированная оценка
        return (length_score * 0.3 + keyword_score * 0.7)
    
    def _calculate_relevance_score(self, answer: str, question: str) -> float:
        """Расчет оценки релевантности ответа"""
        if not answer:
            return 0.0
        
        # Простая эвристика: проверка на наличие общих слов
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        # Исключаем стоп-слова
        stop_words = {"как", "что", "где", "когда", "почему", "который", "какой", "есть", "в", "на", "с", "по", "для", "от", "до", "и", "или", "но", "а", "же", "ли", "бы", "не", "ни", "уже", "еще", "только", "даже", "все", "всего", "всех", "всей", "всему", "всем", "всеми", "всю", "всею", "всея", "всее", "всеи", "всею", "всея", "всее", "всеи"}
        
        question_words = question_words - stop_words
        answer_words = answer_words - stop_words
        
        if not question_words:
            return 0.5  # Нейтральная оценка если нет значимых слов в вопросе
        
        common_words = question_words.intersection(answer_words)
        relevance = len(common_words) / len(question_words)
        
        return min(relevance, 1.0)
    
    def _analyze_results(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        analysis = {
            "model_comparison": {},
            "category_analysis": {},
            "performance_analysis": {},
            "quality_analysis": {}
        }
        
        # Сравнение моделей
        for model_name, results in all_results.items():
            metrics = results["overall_metrics"]
            analysis["model_comparison"][model_name] = {
                "accuracy": metrics["average_accuracy"],
                "completeness": metrics["average_completeness"],
                "relevance": metrics["average_relevance"],
                "response_time": metrics["average_response_time"],
                "total_questions": metrics["total_questions"]
            }
        
        # Анализ по категориям
        categories = set()
        for results in all_results.values():
            for result in results["test_results"]:
                # Извлекаем категорию из вопроса (упрощенно)
                if "трафик" in result.question.lower():
                    categories.add("traffic")
                elif "договор" in result.question.lower():
                    categories.add("agreements")
                elif "отчет" in result.question.lower():
                    categories.add("reports")
                else:
                    categories.add("general")
        
        for category in categories:
            analysis["category_analysis"][category] = {
                "questions_count": 0,
                "average_accuracy": 0.0,
                "average_response_time": 0.0
            }
        
        # Анализ производительности
        response_times = []
        for results in all_results.values():
            for result in results["test_results"]:
                response_times.append(result.response_time)
        
        if response_times:
            analysis["performance_analysis"] = {
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "avg_response_time": sum(response_times) / len(response_times),
                "slow_queries_count": len([t for t in response_times if t > 10.0])
            }
        
        return analysis
    
    def _save_test_results(self, all_results: Dict[str, Any], analysis: Dict[str, Any]):
        """Сохранение результатов тестирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/mnt/ai/cnn/steccom/tests/kb_effectiveness_results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "test_results": all_results,
            "analysis": analysis,
            "summary": self._generate_summary(analysis)
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результаты сохранены в: {results_file}")
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация краткого резюме результатов"""
        if not analysis.get("model_comparison"):
            return {"error": "Нет данных для анализа"}
        
        # Находим лучшую модель по каждому критерию
        best_accuracy = max(analysis["model_comparison"].items(), key=lambda x: x[1]["accuracy"])
        best_speed = min(analysis["model_comparison"].items(), key=lambda x: x[1]["response_time"])
        
        return {
            "best_accuracy_model": best_accuracy[0],
            "best_accuracy_score": best_accuracy[1]["accuracy"],
            "fastest_model": best_speed[0],
            "fastest_response_time": best_speed[1]["response_time"],
            "total_models_tested": len(analysis["model_comparison"]),
            "performance_issues": analysis.get("performance_analysis", {}).get("slow_queries_count", 0)
        }


class TestKBEffectiveness:
    """Основные тесты эффективности Knowledge Base"""
    
    @pytest.fixture(autouse=True)
    def setup_tester(self):
        """Инициализация тестера"""
        self.tester = KBEffectivenessTester()
        # Проверяем, что KB загружены
        assert len(self.tester.rag.vectorstores) > 0, "No knowledge bases loaded"
    
    def test_kb_accuracy_gpt4o(self):
        """Тест точности KB с GPT-4o"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что точность выше 70%
        assert results["overall_metrics"]["average_accuracy"] > 0.7, \
            f"Accuracy too low: {results['overall_metrics']['average_accuracy']:.2f}"
        
        # Проверяем, что время ответа разумное
        assert results["overall_metrics"]["average_response_time"] < 30.0, \
            f"Response time too slow: {results['overall_metrics']['average_response_time']:.2f}s"
    
    def test_kb_accuracy_qwen(self):
        """Тест точности KB с Qwen"""
        config = {"provider": "ollama", "model": "qwen2.5:1.5b", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что точность выше 60% (Qwen может быть менее точным)
        assert results["overall_metrics"]["average_accuracy"] > 0.6, \
            f"Accuracy too low: {results['overall_metrics']['average_accuracy']:.2f}"
        
        # Проверяем, что время ответа разумное
        assert results["overall_metrics"]["average_response_time"] < 15.0, \
            f"Response time too slow: {results['overall_metrics']['average_response_time']:.2f}s"
    
    def test_kb_completeness(self):
        """Тест полноты покрытия KB"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что полнота выше 60%
        assert results["overall_metrics"]["average_completeness"] > 0.6, \
            f"Completeness too low: {results['overall_metrics']['average_completeness']:.2f}"
    
    def test_kb_relevance(self):
        """Тест релевантности ответов KB"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что релевантность выше 50%
        assert results["overall_metrics"]["average_relevance"] > 0.5, \
            f"Relevance too low: {results['overall_metrics']['average_relevance']:.2f}"
    
    def test_kb_performance_benchmark(self):
        """Бенчмарк производительности KB"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что большинство запросов выполняются быстро
        slow_queries = 0
        for result in results["test_results"]:
            if result.response_time > 10.0:
                slow_queries += 1
        
        slow_percentage = slow_queries / len(results["test_results"]) * 100
        assert slow_percentage < 20, \
            f"Too many slow queries: {slow_percentage:.1f}% > 20%"
    
    def test_kb_model_comparison(self):
        """Сравнительный тест моделей"""
        configs = [
            {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0},
            {"provider": "ollama", "model": "qwen2.5:1.5b", "temperature": 0.0}
        ]
        
        results = self.tester.run_comprehensive_effectiveness_test(configs)
        
        # Проверяем, что обе модели дали результаты
        assert len(results["model_results"]) == 2, "Should test both models"
        
        # Проверяем, что GPT-4o точнее Qwen
        gpt4o_results = results["model_results"]["proxyapi_gpt-4o"]["overall_metrics"]
        qwen_results = results["model_results"]["ollama_qwen2.5:1.5b"]["overall_metrics"]
        
        assert gpt4o_results["average_accuracy"] >= qwen_results["average_accuracy"], \
            "GPT-4o should be at least as accurate as Qwen"
    
    def test_kb_coverage_analysis(self):
        """Тест покрытия различных категорий знаний"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что все категории вопросов покрыты
        categories_tested = set()
        for result in results["test_results"]:
            if "трафик" in result.question.lower():
                categories_tested.add("traffic")
            elif "договор" in result.question.lower():
                categories_tested.add("agreements")
            elif "отчет" in result.question.lower():
                categories_tested.add("reports")
            else:
                categories_tested.add("general")
        
        assert len(categories_tested) >= 3, f"Not enough categories covered: {categories_tested}"
    
    def test_kb_quality_consistency(self):
        """Тест консистентности качества ответов"""
        config = {"provider": "proxyapi", "model": "gpt-4o", "temperature": 0.0}
        results = self.tester._test_model_effectiveness(config)
        
        # Проверяем, что нет ответов с нулевой оценкой
        zero_quality_count = 0
        for result in results["test_results"]:
            if result.accuracy_score == 0.0 and result.completeness_score == 0.0:
                zero_quality_count += 1
        
        zero_percentage = zero_quality_count / len(results["test_results"]) * 100
        assert zero_percentage < 10, \
            f"Too many zero-quality responses: {zero_percentage:.1f}% > 10%"
    
    def test_kb_protocol_testing(self):
        """Тест протоколирования тестирования KB"""
        # Запуск тестирования с протоколированием
        protocol_file = self.tester.run_protocol_test()
        
        # Проверяем, что протокол создан
        assert os.path.exists(protocol_file), "Protocol file should be created"
        
        # Проверяем содержимое протокола
        with open(protocol_file, 'r', encoding='utf-8') as f:
            protocol_data = json.load(f)
        
        assert "protocol_info" in protocol_data, "Protocol should have info section"
        assert "test_entries" in protocol_data, "Protocol should have test entries"
        assert "summary_statistics" in protocol_data, "Protocol should have summary statistics"
        
        # Проверяем, что есть записи тестов
        assert len(protocol_data["test_entries"]) > 0, "Should have test entries"
        
        # Проверяем структуру записей
        for entry in protocol_data["test_entries"]:
            assert "question" in entry, "Entry should have question"
            assert "model_response" in entry, "Entry should have model response"
            assert "relevance_assessment" in entry, "Entry should have relevance assessment"
            
            # Проверяем оценки
            assessment = entry["relevance_assessment"]
            assert 0.0 <= assessment["accuracy_score"] <= 1.0, "Accuracy score should be 0-1"
            assert 0.0 <= assessment["completeness_score"] <= 1.0, "Completeness score should be 0-1"
            assert 0.0 <= assessment["relevance_score"] <= 1.0, "Relevance score should be 0-1"
        
        print(f"✅ Протокол тестирования создан: {protocol_file}")


if __name__ == "__main__":
    # Запуск тестов с подробным выводом
    print("🧪 Запуск тестов эффективности Knowledge Base...")
    pytest.main([__file__, "-v", "-s", "--tb=short"])
