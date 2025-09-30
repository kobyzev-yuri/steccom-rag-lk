"""
Relevance Analysis Module
Модуль анализа релевантности ответов KB
"""

import re
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from ..core.knowledge_manager import KnowledgeBaseManager
from ..rag.multi_kb_rag import MultiKBRAG
from .kb_test_protocol import KBTestProtocol, TestQuestion, ModelResponse, RelevanceAssessment


@dataclass
class RelevanceTestResult:
    """Результат теста релевантности"""
    question: str
    expected_keywords: List[str]
    actual_answer: str
    response_time: float
    sources_found: int
    accuracy_score: float
    completeness_score: float
    relevance_score: float
    overall_quality: str
    model_used: str
    timestamp: str
    recommendations: List[str]


class RelevanceAnalyzer:
    """Анализатор релевантности ответов KB"""
    
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()
        self.protocol = KBTestProtocol()
        
        # Инициализация RAG системы
        self.rag = MultiKBRAG()
        
        # Веса для оценки качества
        self.quality_weights = {
            "accuracy": 0.4,
            "completeness": 0.3,
            "relevance": 0.3
        }
    
    def test_kb_relevance(self, kb_id: int, test_questions: List[Dict[str, Any]] = None) -> List[RelevanceTestResult]:
        """Тестирование релевантности KB"""
        
        if test_questions is None:
            test_questions = self._get_default_test_questions()
        
        results = []
        
        # Загружаем KB в RAG систему
        try:
            self.rag.load_all_active_kbs()
        except Exception as e:
            print(f"Ошибка загрузки KB: {e}")
            return results
        
        for question_data in test_questions:
            try:
                result = self._test_single_question(question_data)
                results.append(result)
            except Exception as e:
                print(f"Ошибка тестирования вопроса: {e}")
                continue
        
        return results
    
    def _test_single_question(self, question_data: Dict[str, Any]) -> RelevanceTestResult:
        """Тестирование одного вопроса"""
        
        question_text = question_data["question"]
        expected_keywords = question_data["expected_keywords"]
        category = question_data.get("category", "general")
        
        # Выполняем поиск
        start_time = time.time()
        try:
            search_result = self.rag.ask_question(question_text)
            response_time = time.time() - start_time
            
            answer = search_result.get("answer", "")
            sources = search_result.get("sources", [])
            
        except Exception as e:
            response_time = time.time() - start_time
            answer = f"Ошибка: {str(e)}"
            sources = []
        
        # Анализируем релевантность
        accuracy_score = self._calculate_accuracy_score(answer, expected_keywords)
        completeness_score = self._calculate_completeness_score(answer, expected_keywords)
        relevance_score = self._calculate_relevance_score(answer, question_text)
        
        # Определяем общее качество
        overall_quality = self._determine_overall_quality(
            accuracy_score, completeness_score, relevance_score
        )
        
        # Генерируем рекомендации
        recommendations = self._generate_recommendations(
            accuracy_score, completeness_score, relevance_score, answer, expected_keywords
        )
        
        return RelevanceTestResult(
            question=question_text,
            expected_keywords=expected_keywords,
            actual_answer=answer,
            response_time=response_time,
            sources_found=len(sources),
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            overall_quality=overall_quality,
            model_used="gpt-4o",  # TODO: получать из настроек
            timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
    
    def _calculate_accuracy_score(self, answer: str, expected_keywords: List[str]) -> float:
        """Расчет точности ответа"""
        if not answer or not expected_keywords:
            return 0.0
        
        answer_lower = answer.lower()
        found_keywords = 0
        
        for keyword in expected_keywords:
            if keyword.lower() in answer_lower:
                found_keywords += 1
        
        return found_keywords / len(expected_keywords)
    
    def _calculate_completeness_score(self, answer: str, expected_keywords: List[str]) -> float:
        """Расчет полноты ответа"""
        if not answer:
            return 0.0
        
        # Проверяем длину ответа
        length_score = min(1.0, len(answer) / 200)  # Нормализуем к 200 символам
        
        # Проверяем наличие ключевых слов
        keyword_score = self._calculate_accuracy_score(answer, expected_keywords)
        
        # Проверяем структурированность ответа
        structure_score = self._calculate_structure_score(answer)
        
        # Взвешенная сумма
        return (length_score * 0.3 + keyword_score * 0.5 + structure_score * 0.2)
    
    def _calculate_relevance_score(self, answer: str, question: str) -> float:
        """Расчет релевантности ответа"""
        if not answer or not question:
            return 0.0
        
        # Извлекаем ключевые слова из вопроса
        question_keywords = self._extract_keywords(question)
        
        # Проверяем, насколько ответ соответствует вопросу
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Простая проверка на соответствие темы
        topic_match = 0.0
        for keyword in question_keywords:
            if keyword in answer_lower:
                topic_match += 1
        
        if question_keywords:
            topic_match = topic_match / len(question_keywords)
        
        # Проверяем, отвечает ли ответ на вопрос
        answer_quality = self._assess_answer_quality(answer, question)
        
        return (topic_match * 0.6 + answer_quality * 0.4)
    
    def _calculate_structure_score(self, answer: str) -> float:
        """Расчет структурированности ответа"""
        if not answer:
            return 0.0
        
        score = 0.0
        
        # Проверяем наличие предложений
        sentences = re.split(r'[.!?]+', answer)
        if len(sentences) > 1:
            score += 0.3
        
        # Проверяем наличие списков
        if re.search(r'[•\-\*]\s+', answer) or re.search(r'\d+\.\s+', answer):
            score += 0.3
        
        # Проверяем наличие абзацев
        if '\n\n' in answer:
            score += 0.2
        
        # Проверяем длину предложений (не слишком короткие, не слишком длинные)
        avg_sentence_length = len(answer) / max(1, len(sentences))
        if 20 <= avg_sentence_length <= 100:
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простая реализация - можно улучшить с помощью NLP библиотек
        words = re.findall(r'\b[а-яё]{3,}\b', text.lower())
        
        # Фильтруем стоп-слова
        stop_words = {'как', 'что', 'где', 'когда', 'почему', 'какой', 'какая', 'какое', 'какие'}
        keywords = [word for word in words if word not in stop_words]
        
        # Возвращаем уникальные слова
        return list(set(keywords))
    
    def _assess_answer_quality(self, answer: str, question: str) -> float:
        """Оценка качества ответа"""
        if not answer:
            return 0.0
        
        score = 0.0
        
        # Проверяем, не является ли ответ слишком коротким
        if len(answer) < 20:
            return 0.2
        
        # Проверяем, не является ли ответ слишком длинным
        if len(answer) > 1000:
            score += 0.1
        else:
            score += 0.3
        
        # Проверяем наличие конкретной информации
        if re.search(r'\d+', answer):  # Есть числа
            score += 0.2
        
        if re.search(r'[А-Я][а-я]+', answer):  # Есть заглавные буквы (возможно, названия)
            score += 0.2
        
        # Проверяем, отвечает ли на вопрос
        question_words = set(re.findall(r'\b[а-яё]+\b', question.lower()))
        answer_words = set(re.findall(r'\b[а-яё]+\b', answer.lower()))
        
        if question_words and answer_words:
            overlap = len(question_words.intersection(answer_words))
            word_overlap_score = overlap / len(question_words)
            score += word_overlap_score * 0.3
        
        return min(1.0, score)
    
    def _determine_overall_quality(self, accuracy: float, completeness: float, relevance: float) -> str:
        """Определение общего качества ответа"""
        overall_score = (
            accuracy * self.quality_weights["accuracy"] +
            completeness * self.quality_weights["completeness"] +
            relevance * self.quality_weights["relevance"]
        )
        
        if overall_score >= 0.8:
            return "excellent"
        elif overall_score >= 0.6:
            return "good"
        elif overall_score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(self, accuracy: float, completeness: float, 
                                relevance: float, answer: str, expected_keywords: List[str]) -> List[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []
        
        if accuracy < 0.6:
            missing_keywords = [kw for kw in expected_keywords if kw.lower() not in answer.lower()]
            if missing_keywords:
                recommendations.append(f"Добавить информацию о: {', '.join(missing_keywords[:3])}")
        
        if completeness < 0.6:
            if len(answer) < 100:
                recommendations.append("Расширить ответ дополнительными деталями")
            else:
                recommendations.append("Улучшить структуру ответа")
        
        if relevance < 0.6:
            recommendations.append("Сделать ответ более релевантным к вопросу")
        
        if not recommendations:
            recommendations.append("Качество ответа хорошее")
        
        return recommendations
    
    def _get_default_test_questions(self) -> List[Dict[str, Any]]:
        """Получение стандартных тестовых вопросов"""
        return [
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
            },
            {
                "question": "Какие возможности есть в личном кабинете?",
                "expected_keywords": ["аналитика", "трафик", "договоры", "мониторинг", "устройств"],
                "category": "ui_capabilities"
            }
        ]
    
    def generate_relevance_report(self, results: List[RelevanceTestResult]) -> Dict[str, Any]:
        """Генерация отчета по релевантности"""
        if not results:
            return {"error": "No test results available"}
        
        # Статистика
        total_tests = len(results)
        avg_accuracy = sum(r.accuracy_score for r in results) / total_tests
        avg_completeness = sum(r.completeness_score for r in results) / total_tests
        avg_relevance = sum(r.relevance_score for r in results) / total_tests
        avg_response_time = sum(r.response_time for r in results) / total_tests
        
        # Распределение по качеству
        quality_distribution = {}
        for result in results:
            quality = result.overall_quality
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        # Проблемные области
        problem_areas = []
        for result in results:
            if result.overall_quality in ["poor", "fair"]:
                problem_areas.append({
                    "question": result.question,
                    "quality": result.overall_quality,
                    "recommendations": result.recommendations
                })
        
        return {
            "summary": {
                "total_tests": total_tests,
                "average_accuracy": round(avg_accuracy, 3),
                "average_completeness": round(avg_completeness, 3),
                "average_relevance": round(avg_relevance, 3),
                "average_response_time": round(avg_response_time, 2),
                "overall_quality": self._determine_overall_quality(avg_accuracy, avg_completeness, avg_relevance)
            },
            "quality_distribution": quality_distribution,
            "problem_areas": problem_areas,
            "recommendations": self._generate_system_recommendations(results)
        }
    
    def _generate_system_recommendations(self, results: List[RelevanceTestResult]) -> List[str]:
        """Генерация системных рекомендаций"""
        recommendations = []
        
        # Анализ общих проблем
        poor_results = [r for r in results if r.overall_quality == "poor"]
        fair_results = [r for r in results if r.overall_quality == "fair"]
        
        if len(poor_results) > len(results) * 0.3:
            recommendations.append("Критический уровень качества: требуется пересмотр настройки чанков")
        
        if len(fair_results) > len(results) * 0.4:
            recommendations.append("Средний уровень качества: рекомендуется оптимизация RAG системы")
        
        # Анализ времени ответа
        avg_time = sum(r.response_time for r in results) / len(results)
        if avg_time > 10:
            recommendations.append("Медленные ответы: оптимизируйте размер чанков или модель")
        
        # Анализ источников
        avg_sources = sum(r.sources_found for r in results) / len(results)
        if avg_sources < 2:
            recommendations.append("Мало источников: увеличьте количество релевантных документов")
        
        if not recommendations:
            recommendations.append("Система работает хорошо, продолжайте мониторинг")
        
        return recommendations
