#!/usr/bin/env python3
"""
Тест агентов для текстового анализа и SQL запросов
Сравнение разных моделей Ollama
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules"))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentsTester:
    """Тестер агентов для анализа текста и SQL"""
    
    def __init__(self):
        self.results = {}
        self.models_to_test = [
            "qwen2.5-coder:7b",
            "qwen3:8b", 
            "llama3:8b",
            "llama3.1:8b"
        ]
        
    def test_sql_agent(self, model_name: str) -> Dict[str, Any]:
        """Тест SQL агента"""
        logger.info(f"🔍 Тестируем SQL агент с моделью {model_name}")
        
        try:
            from modules.core.rag import generate_sql
            
            # Тестовые вопросы для SQL
            test_questions = [
                "Покажи SBD трафик за май месяц по каждому устройству",
                "Сколько потратили на VSAT_DATA в прошлом месяце?",
                "Какие устройства используют больше всего трафика?",
                "Покажи статистику по всем сервисам за последние 3 месяца"
            ]
            
            results = []
            total_time = 0
            successful_queries = 0
            
            for i, question in enumerate(test_questions):
                logger.info(f"  📝 Вопрос {i+1}: {question}")
                
                start_time = time.time()
                try:
                    # Генерируем SQL запрос
                    sql_query = generate_sql(question, "test_company")
                    query_time = time.time() - start_time
                    total_time += query_time
                    
                    if sql_query and len(sql_query.strip()) > 10:
                        successful_queries += 1
                        logger.info(f"    ✅ SQL сгенерирован за {query_time:.2f}с")
                    else:
                        logger.warning(f"    ⚠️ Пустой или короткий SQL")
                    
                    results.append({
                        'question': question,
                        'sql_query': sql_query,
                        'time': query_time,
                        'success': bool(sql_query and len(sql_query.strip()) > 10)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка SQL: {e}")
                    results.append({
                        'question': question,
                        'sql_query': '',
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            success_rate = successful_queries / len(test_questions)
            avg_time = total_time / len(test_questions)
            
            return {
                'model': model_name,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'total_time': total_time,
                'successful_queries': successful_queries,
                'total_questions': len(test_questions),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка SQL агента: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def test_text_analysis(self, model_name: str) -> Dict[str, Any]:
        """Тест текстового анализа"""
        logger.info(f"📝 Тестируем текстовый анализ с моделью {model_name}")
        
        try:
            from modules.core.base_agent import BaseAgent
            
            # Создаем агента для текстового анализа
            agent = BaseAgent(
                agent_name=f"text_analyzer_{model_name.replace(':', '_')}",
                model_type="document_analysis"
            )
            agent.model_name = model_name
            agent._init_chat_model()
            
            # Тестовые тексты для анализа
            test_texts = [
                "Техническая документация по спутниковой связи содержит подробные инструкции по настройке оборудования и протоколы передачи данных.",
                "SBD (Short Burst Data) - это технология передачи коротких сообщений через спутниковую сеть с минимальным потреблением энергии.",
                "VSAT система обеспечивает высокоскоростной доступ в интернет через геостационарные спутники с пропускной способностью до 100 Мбит/с."
            ]
            
            results = []
            total_time = 0
            successful_analyses = 0
            
            for i, text in enumerate(test_texts):
                logger.info(f"  📄 Текст {i+1}: {text[:50]}...")
                
                prompt = f"""Проанализируй следующий текст и определи:
1. Тип документа (технический, инструкция, описание и т.д.)
2. Ключевые термины и понятия
3. Уровень технической сложности
4. Основную тему

Текст: {text}

Ответь структурированно на русском языке."""
                
                start_time = time.time()
                try:
                    # Анализируем текст
                    response = agent.chat_model.invoke(prompt)
                    analysis_time = time.time() - start_time
                    total_time += analysis_time
                    
                    if response and len(str(response.content).strip()) > 20:
                        successful_analyses += 1
                        logger.info(f"    ✅ Анализ выполнен за {analysis_time:.2f}с")
                    else:
                        logger.warning(f"    ⚠️ Короткий или пустой ответ")
                    
                    results.append({
                        'text': text,
                        'analysis': str(response.content) if hasattr(response, 'content') else str(response),
                        'time': analysis_time,
                        'success': bool(response and len(str(response.content).strip()) > 20)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка анализа: {e}")
                    results.append({
                        'text': text,
                        'analysis': '',
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            success_rate = successful_analyses / len(test_texts)
            avg_time = total_time / len(test_texts)
            
            return {
                'model': model_name,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'total_time': total_time,
                'successful_analyses': successful_analyses,
                'total_texts': len(test_texts),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка текстового анализа: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def test_chat_agent(self, model_name: str) -> Dict[str, Any]:
        """Тест чат агента"""
        logger.info(f"💬 Тестируем чат агент с моделью {model_name}")
        
        try:
            from modules.core.base_agent import BaseAgent
            
            # Создаем чат агента
            agent = BaseAgent(
                agent_name=f"chat_agent_{model_name.replace(':', '_')}",
                model_type="chat"
            )
            agent.model_name = model_name
            agent._init_chat_model()
            
            # Тестовые вопросы
            test_questions = [
                "Что такое SBD пакет в спутниковой связи?",
                "Как работает VSAT система?",
                "Объясни разницу между SBD и VSAT_DATA",
                "Какие преимущества у спутниковой связи?"
            ]
            
            results = []
            total_time = 0
            successful_responses = 0
            
            for i, question in enumerate(test_questions):
                logger.info(f"  ❓ Вопрос {i+1}: {question}")
                
                start_time = time.time()
                try:
                    # Получаем ответ
                    response = agent.chat_model.invoke(question)
                    response_time = time.time() - start_time
                    total_time += response_time
                    
                    if response and len(str(response.content).strip()) > 20:
                        successful_responses += 1
                        logger.info(f"    ✅ Ответ получен за {response_time:.2f}с")
                    else:
                        logger.warning(f"    ⚠️ Короткий или пустой ответ")
                    
                    results.append({
                        'question': question,
                        'answer': str(response.content) if hasattr(response, 'content') else str(response),
                        'time': response_time,
                        'success': bool(response and len(str(response.content).strip()) > 20)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка ответа: {e}")
                    results.append({
                        'question': question,
                        'answer': '',
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            success_rate = successful_responses / len(test_questions)
            avg_time = total_time / len(test_questions)
            
            return {
                'model': model_name,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'total_time': total_time,
                'successful_responses': successful_responses,
                'total_questions': len(test_questions),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка чат агента: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования всех агентов"""
        logger.info("🚀 Запуск комплексного тестирования агентов")
        
        all_results = {
            'test_date': datetime.now().isoformat(),
            'models_tested': self.models_to_test,
            'sql_results': {},
            'text_analysis_results': {},
            'chat_results': {},
            'summary': {}
        }
        
        for model in self.models_to_test:
            logger.info(f"\n{'='*50}")
            logger.info(f"🧪 ТЕСТИРУЕМ МОДЕЛЬ: {model}")
            logger.info(f"{'='*50}")
            
            # Тест SQL агента
            logger.info(f"\n📊 SQL АГЕНТ - {model}")
            sql_result = self.test_sql_agent(model)
            all_results['sql_results'][model] = sql_result
            
            # Тест текстового анализа
            logger.info(f"\n📝 ТЕКСТОВЫЙ АНАЛИЗ - {model}")
            text_result = self.test_text_analysis(model)
            all_results['text_analysis_results'][model] = text_result
            
            # Тест чат агента
            logger.info(f"\n💬 ЧАТ АГЕНТ - {model}")
            chat_result = self.test_chat_agent(model)
            all_results['chat_results'][model] = chat_result
        
        # Анализ результатов
        all_results['summary'] = self._analyze_results(all_results)
        
        # Сохранение результатов
        self._save_results(all_results)
        
        return all_results
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        summary = {
            'best_sql_model': None,
            'best_text_model': None,
            'best_chat_model': None,
            'overall_best_model': None,
            'recommendations': []
        }
        
        # Анализ SQL результатов
        sql_scores = {}
        for model, result in results['sql_results'].items():
            if result.get('success_rate', 0) > 0:
                sql_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if sql_scores:
            summary['best_sql_model'] = max(sql_scores, key=sql_scores.get)
        
        # Анализ текстового анализа
        text_scores = {}
        for model, result in results['text_analysis_results'].items():
            if result.get('success_rate', 0) > 0:
                text_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if text_scores:
            summary['best_text_model'] = max(text_scores, key=text_scores.get)
        
        # Анализ чат результатов
        chat_scores = {}
        for model, result in results['chat_results'].items():
            if result.get('success_rate', 0) > 0:
                chat_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if chat_scores:
            summary['best_chat_model'] = max(chat_scores, key=chat_scores.get)
        
        # Общий анализ
        overall_scores = {}
        for model in results['models_tested']:
            sql_score = results['sql_results'].get(model, {}).get('success_rate', 0)
            text_score = results['text_analysis_results'].get(model, {}).get('success_rate', 0)
            chat_score = results['chat_results'].get(model, {}).get('success_rate', 0)
            
            overall_scores[model] = (sql_score + text_score + chat_score) / 3
        
        if overall_scores:
            summary['overall_best_model'] = max(overall_scores, key=overall_scores.get)
        
        # Генерация рекомендаций
        if summary['overall_best_model']:
            summary['recommendations'].append(f"Лучшая общая модель: {summary['overall_best_model']}")
        
        if summary['best_sql_model']:
            summary['recommendations'].append(f"Лучшая для SQL: {summary['best_sql_model']}")
        
        if summary['best_text_model']:
            summary['recommendations'].append(f"Лучшая для текста: {summary['best_text_model']}")
        
        if summary['best_chat_model']:
            summary['recommendations'].append(f"Лучшая для чата: {summary['best_chat_model']}")
        
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """Сохранение результатов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agents_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Вывод краткого отчета"""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ АГЕНТОВ")
        print("="*60)
        
        summary = results['summary']
        
        print(f"📅 Дата тестирования: {results['test_date']}")
        print(f"🤖 Моделей протестировано: {len(results['models_tested'])}")
        
        print(f"\n🏆 ЛУЧШИЕ МОДЕЛИ:")
        if summary.get('overall_best_model'):
            print(f"  🥇 Общая: {summary['overall_best_model']}")
        if summary.get('best_sql_model'):
            print(f"  📊 SQL: {summary['best_sql_model']}")
        if summary.get('best_text_model'):
            print(f"  📝 Текст: {summary['best_text_model']}")
        if summary.get('best_chat_model'):
            print(f"  💬 Чат: {summary['best_chat_model']}")
        
        print(f"\n📋 РЕКОМЕНДАЦИИ:")
        for rec in summary.get('recommendations', []):
            print(f"  • {rec}")
        
        print("="*60)

def main():
    """Основная функция"""
    print("🧪 ТЕСТИРОВАНИЕ АГЕНТОВ KB ADMIN")
    print("=" * 50)
    
    try:
        tester = AgentsTester()
        results = tester.run_comprehensive_test()
        tester.print_summary(results)
        
        print(f"\n🎉 Тестирование завершено!")
        print(f"📄 Результаты сохранены в JSON файл")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        return 1
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)







