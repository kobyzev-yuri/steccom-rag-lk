#!/usr/bin/env python3
"""
Тест ключевых агентов KB Admin:
1. RAG Admin - MultiKBRAG для работы с базами знаний
2. SQL Assistant - для SQL запросов
3. Smart Librarian - умный библиотекарь для RAG ответов
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

class KeyAgentsTester:
    """Тестер ключевых агентов KB Admin"""
    
    def __init__(self):
        self.results = {}
        self.models_to_test = [
            "qwen2.5-coder:7b",
            "qwen3:8b", 
            "llama3:8b",
            "llama3.1:8b"
        ]
        
    def test_rag_admin(self, model_name: str) -> Dict[str, Any]:
        """Тест RAG Admin агента"""
        logger.info(f"🧠 Тестируем RAG Admin с моделью {model_name}")
        
        try:
            from modules.rag.multi_kb_rag import MultiKBRAG
            
            # Создаем RAG систему
            rag = MultiKBRAG()
            
            # Тестовые вопросы для RAG
            test_questions = [
                "Что такое SBD пакет в спутниковой связи?",
                "Как работает VSAT система?",
                "Какие преимущества у спутниковой связи?",
                "Объясни протокол передачи данных через спутник"
            ]
            
            results = []
            total_time = 0
            successful_answers = 0
            
            for i, question in enumerate(test_questions):
                logger.info(f"  ❓ Вопрос {i+1}: {question}")
                
                start_time = time.time()
                try:
                    # Загружаем базы знаний
                    rag.load_all_active_kbs()
                    
                    # Задаем вопрос
                    response = rag.ask_question(question)
                    response_time = time.time() - start_time
                    total_time += response_time
                    
                    answer = response.get("answer", "")
                    sources = response.get("sources", [])
                    
                    if answer and len(answer.strip()) > 20:
                        successful_answers += 1
                        logger.info(f"    ✅ Ответ получен за {response_time:.2f}с")
                        logger.info(f"    📚 Источников: {len(sources)}")
                    else:
                        logger.warning(f"    ⚠️ Короткий или пустой ответ")
                    
                    results.append({
                        'question': question,
                        'answer': answer,
                        'sources_count': len(sources),
                        'time': response_time,
                        'success': bool(answer and len(answer.strip()) > 20)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка RAG: {e}")
                    results.append({
                        'question': question,
                        'answer': '',
                        'sources_count': 0,
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            success_rate = successful_answers / len(test_questions)
            avg_time = total_time / len(test_questions)
            
            return {
                'model': model_name,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'total_time': total_time,
                'successful_answers': successful_answers,
                'total_questions': len(test_questions),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка RAG Admin: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def test_sql_assistant(self, model_name: str) -> Dict[str, Any]:
        """Тест SQL Assistant агента"""
        logger.info(f"📊 Тестируем SQL Assistant с моделью {model_name}")
        
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
                        logger.info(f"    📄 Длина SQL: {len(sql_query)} символов")
                    else:
                        logger.warning(f"    ⚠️ Пустой или короткий SQL")
                    
                    results.append({
                        'question': question,
                        'sql_query': sql_query,
                        'sql_length': len(sql_query),
                        'time': query_time,
                        'success': bool(sql_query and len(sql_query.strip()) > 10)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка SQL: {e}")
                    results.append({
                        'question': question,
                        'sql_query': '',
                        'sql_length': 0,
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
            logger.error(f"❌ Ошибка SQL Assistant: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def test_smart_librarian(self, model_name: str) -> Dict[str, Any]:
        """Тест Smart Librarian агента"""
        logger.info(f"📚 Тестируем Smart Librarian с моделью {model_name}")
        
        try:
            from modules.core.smart_document_agent import SmartLibrarian
            from modules.core.knowledge_manager import KnowledgeBaseManager
            from modules.documents.pdf_processor import PDFProcessor
            
            # Создаем компоненты для Smart Librarian
            kb_manager = KnowledgeBaseManager()
            pdf_processor = PDFProcessor()
            
            # Создаем Smart Librarian
            librarian = SmartLibrarian(kb_manager, pdf_processor)
            librarian.model_name = model_name
            librarian._init_chat_model()
            
            # Тестовые задачи для Smart Librarian
            test_tasks = [
                {
                    'type': 'document_analysis',
                    'content': 'Техническая документация по спутниковой связи содержит подробные инструкции по настройке оборудования и протоколы передачи данных.',
                    'question': 'Проанализируй этот документ и определи его тип и ключевые темы'
                },
                {
                    'type': 'content_categorization', 
                    'content': 'SBD (Short Burst Data) - это технология передачи коротких сообщений через спутниковую сеть с минимальным потреблением энергии.',
                    'question': 'К какой категории относится этот контент?'
                },
                {
                    'type': 'knowledge_extraction',
                    'content': 'VSAT система обеспечивает высокоскоростной доступ в интернет через геостационарные спутники с пропускной способностью до 100 Мбит/с.',
                    'question': 'Извлеки ключевые технические характеристики из этого текста'
                }
            ]
            
            results = []
            total_time = 0
            successful_tasks = 0
            
            for i, task in enumerate(test_tasks):
                logger.info(f"  📋 Задача {i+1}: {task['type']}")
                
                start_time = time.time()
                try:
                    # Выполняем задачу через Smart Librarian
                    prompt = f"""Тип задачи: {task['type']}
Контент: {task['content']}
Вопрос: {task['question']}

Проанализируй и дай подробный ответ на русском языке."""
                    
                    response = librarian.chat_model.invoke(prompt)
                    task_time = time.time() - start_time
                    total_time += task_time
                    
                    answer = str(response.content) if hasattr(response, 'content') else str(response)
                    
                    if answer and len(answer.strip()) > 20:
                        successful_tasks += 1
                        logger.info(f"    ✅ Задача выполнена за {task_time:.2f}с")
                    else:
                        logger.warning(f"    ⚠️ Короткий или пустой ответ")
                    
                    results.append({
                        'task_type': task['type'],
                        'content': task['content'],
                        'question': task['question'],
                        'answer': answer,
                        'time': task_time,
                        'success': bool(answer and len(answer.strip()) > 20)
                    })
                    
                except Exception as e:
                    logger.error(f"    ❌ Ошибка задачи: {e}")
                    results.append({
                        'task_type': task['type'],
                        'content': task['content'],
                        'question': task['question'],
                        'answer': '',
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            success_rate = successful_tasks / len(test_tasks)
            avg_time = total_time / len(test_tasks)
            
            return {
                'model': model_name,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'total_time': total_time,
                'successful_tasks': successful_tasks,
                'total_tasks': len(test_tasks),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка Smart Librarian: {e}")
            return {
                'model': model_name,
                'success_rate': 0,
                'avg_time': 0,
                'error': str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования ключевых агентов"""
        logger.info("🚀 Запуск тестирования ключевых агентов KB Admin")
        
        all_results = {
            'test_date': datetime.now().isoformat(),
            'models_tested': self.models_to_test,
            'rag_admin_results': {},
            'sql_assistant_results': {},
            'smart_librarian_results': {},
            'summary': {}
        }
        
        for model in self.models_to_test:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 ТЕСТИРУЕМ МОДЕЛЬ: {model}")
            logger.info(f"{'='*60}")
            
            # Тест RAG Admin
            logger.info(f"\n🧠 RAG ADMIN - {model}")
            rag_result = self.test_rag_admin(model)
            all_results['rag_admin_results'][model] = rag_result
            
            # Тест SQL Assistant
            logger.info(f"\n📊 SQL ASSISTANT - {model}")
            sql_result = self.test_sql_assistant(model)
            all_results['sql_assistant_results'][model] = sql_result
            
            # Тест Smart Librarian
            logger.info(f"\n📚 SMART LIBRARIAN - {model}")
            librarian_result = self.test_smart_librarian(model)
            all_results['smart_librarian_results'][model] = librarian_result
        
        # Анализ результатов
        all_results['summary'] = self._analyze_results(all_results)
        
        # Сохранение результатов
        self._save_results(all_results)
        
        return all_results
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ результатов тестирования"""
        summary = {
            'best_rag_model': None,
            'best_sql_model': None,
            'best_librarian_model': None,
            'overall_best_model': None,
            'recommendations': []
        }
        
        # Анализ RAG результатов
        rag_scores = {}
        for model, result in results['rag_admin_results'].items():
            if result.get('success_rate', 0) > 0:
                rag_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if rag_scores:
            summary['best_rag_model'] = max(rag_scores, key=rag_scores.get)
        
        # Анализ SQL результатов
        sql_scores = {}
        for model, result in results['sql_assistant_results'].items():
            if result.get('success_rate', 0) > 0:
                sql_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if sql_scores:
            summary['best_sql_model'] = max(sql_scores, key=sql_scores.get)
        
        # Анализ Smart Librarian результатов
        librarian_scores = {}
        for model, result in results['smart_librarian_results'].items():
            if result.get('success_rate', 0) > 0:
                librarian_scores[model] = result['success_rate'] / (result.get('avg_time', 1) + 1)
        
        if librarian_scores:
            summary['best_librarian_model'] = max(librarian_scores, key=librarian_scores.get)
        
        # Общий анализ
        overall_scores = {}
        for model in results['models_tested']:
            rag_score = results['rag_admin_results'].get(model, {}).get('success_rate', 0)
            sql_score = results['sql_assistant_results'].get(model, {}).get('success_rate', 0)
            librarian_score = results['smart_librarian_results'].get(model, {}).get('success_rate', 0)
            
            overall_scores[model] = (rag_score + sql_score + librarian_score) / 3
        
        if overall_scores:
            summary['overall_best_model'] = max(overall_scores, key=overall_scores.get)
        
        # Генерация рекомендаций
        if summary['overall_best_model']:
            summary['recommendations'].append(f"🏆 Лучшая общая модель: {summary['overall_best_model']}")
        
        if summary['best_rag_model']:
            summary['recommendations'].append(f"🧠 Лучшая для RAG: {summary['best_rag_model']}")
        
        if summary['best_sql_model']:
            summary['recommendations'].append(f"📊 Лучшая для SQL: {summary['best_sql_model']}")
        
        if summary['best_librarian_model']:
            summary['recommendations'].append(f"📚 Лучшая для Smart Librarian: {summary['best_librarian_model']}")
        
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """Сохранение результатов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"key_agents_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Вывод краткого отчета"""
        print("\n" + "="*70)
        print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ КЛЮЧЕВЫХ АГЕНТОВ KB ADMIN")
        print("="*70)
        
        summary = results['summary']
        
        print(f"📅 Дата тестирования: {results['test_date']}")
        print(f"🤖 Моделей протестировано: {len(results['models_tested'])}")
        
        print(f"\n🏆 ЛУЧШИЕ МОДЕЛИ ПО АГЕНТАМ:")
        if summary.get('best_rag_model'):
            print(f"  🧠 RAG Admin: {summary['best_rag_model']}")
        if summary.get('best_sql_model'):
            print(f"  📊 SQL Assistant: {summary['best_sql_model']}")
        if summary.get('best_librarian_model'):
            print(f"  📚 Smart Librarian: {summary['best_librarian_model']}")
        
        if summary.get('overall_best_model'):
            print(f"\n🥇 ОБЩИЙ ПОБЕДИТЕЛЬ: {summary['overall_best_model']}")
        
        print(f"\n📋 РЕКОМЕНДАЦИИ:")
        for rec in summary.get('recommendations', []):
            print(f"  • {rec}")
        
        print("="*70)

def main():
    """Основная функция"""
    print("🧪 ТЕСТИРОВАНИЕ КЛЮЧЕВЫХ АГЕНТОВ KB ADMIN")
    print("=" * 50)
    print("Тестируем:")
    print("  🧠 RAG Admin - работа с базами знаний")
    print("  📊 SQL Assistant - генерация SQL запросов")
    print("  📚 Smart Librarian - анализ документов и RAG ответы")
    print("=" * 50)
    
    try:
        tester = KeyAgentsTester()
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







