#!/usr/bin/env python3
"""
Быстрый тест ключевых агентов - только по 1 вопросу на модель
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules"))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickAgentsTester:
    """Быстрый тестер агентов"""
    
    def __init__(self):
        self.models_to_test = ["qwen3:8b", "llama3:8b"]  # Только 2 модели
        
    def test_sql_assistant_quick(self, model_name: str) -> Dict[str, Any]:
        """Быстрый тест SQL Assistant"""
        logger.info(f"📊 Быстрый тест SQL Assistant: {model_name}")
        
        try:
            from modules.core.rag import generate_sql
            
            # Только 1 простой вопрос
            question = "Покажи SBD трафик за май месяц"
            
            start_time = time.time()
            try:
                sql_query = generate_sql(question, "test_company")
                query_time = time.time() - start_time
                
                success = bool(sql_query and len(sql_query.strip()) > 10)
                
                return {
                    'model': model_name,
                    'success': success,
                    'time': query_time,
                    'sql_length': len(sql_query) if sql_query else 0,
                    'sql_preview': sql_query[:100] + "..." if sql_query and len(sql_query) > 100 else sql_query
                }
                
            except Exception as e:
                return {
                    'model': model_name,
                    'success': False,
                    'time': time.time() - start_time,
                    'error': str(e)
                }
                
        except Exception as e:
            return {
                'model': model_name,
                'success': False,
                'time': 0,
                'error': str(e)
            }
    
    def test_chat_agent_quick(self, model_name: str) -> Dict[str, Any]:
        """Быстрый тест чат агента"""
        logger.info(f"💬 Быстрый тест чат агента: {model_name}")
        
        try:
            from modules.core.base_agent import BaseAgent
            
            # Создаем чат агента
            agent = BaseAgent(
                agent_name=f"quick_chat_{model_name.replace(':', '_')}",
                model_type="chat"
            )
            agent.model_name = model_name
            agent._init_chat_model()
            
            # Только 1 простой вопрос
            question = "Что такое SBD в спутниковой связи?"
            
            start_time = time.time()
            try:
                response = agent.chat_model.invoke(question)
                response_time = time.time() - start_time
                
                answer = str(response.content) if hasattr(response, 'content') else str(response)
                success = bool(answer and len(answer.strip()) > 20)
                
                return {
                    'model': model_name,
                    'success': success,
                    'time': response_time,
                    'answer_length': len(answer) if answer else 0,
                    'answer_preview': answer[:100] + "..." if answer and len(answer) > 100 else answer
                }
                
            except Exception as e:
                return {
                    'model': model_name,
                    'success': False,
                    'time': time.time() - start_time,
                    'error': str(e)
                }
                
        except Exception as e:
            return {
                'model': model_name,
                'success': False,
                'time': 0,
                'error': str(e)
            }
    
    def run_quick_test(self) -> Dict[str, Any]:
        """Запуск быстрого теста"""
        logger.info("🚀 БЫСТРЫЙ ТЕСТ АГЕНТОВ")
        
        results = {
            'test_date': datetime.now().isoformat(),
            'models_tested': self.models_to_test,
            'sql_results': {},
            'chat_results': {},
            'summary': {}
        }
        
        for model in self.models_to_test:
            logger.info(f"\n{'='*40}")
            logger.info(f"🧪 МОДЕЛЬ: {model}")
            logger.info(f"{'='*40}")
            
            # Тест SQL
            logger.info(f"📊 Тестируем SQL...")
            sql_result = self.test_sql_assistant_quick(model)
            results['sql_results'][model] = sql_result
            
            if sql_result['success']:
                logger.info(f"  ✅ SQL работает за {sql_result['time']:.2f}с")
            else:
                logger.info(f"  ❌ SQL ошибка: {sql_result.get('error', 'Неизвестно')}")
            
            # Тест чат
            logger.info(f"💬 Тестируем чат...")
            chat_result = self.test_chat_agent_quick(model)
            results['chat_results'][model] = chat_result
            
            if chat_result['success']:
                logger.info(f"  ✅ Чат работает за {chat_result['time']:.2f}с")
            else:
                logger.info(f"  ❌ Чат ошибка: {chat_result.get('error', 'Неизвестно')}")
        
        # Анализ результатов
        results['summary'] = self._analyze_quick_results(results)
        
        # Сохранение
        self._save_quick_results(results)
        
        return results
    
    def _analyze_quick_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ быстрых результатов"""
        summary = {
            'working_models': [],
            'best_sql_model': None,
            'best_chat_model': None,
            'recommendations': []
        }
        
        # Анализ SQL
        sql_models = []
        for model, result in results['sql_results'].items():
            if result['success']:
                sql_models.append((model, result['time']))
        
        if sql_models:
            summary['best_sql_model'] = min(sql_models, key=lambda x: x[1])[0]
            summary['working_models'].extend([m[0] for m in sql_models])
        
        # Анализ чат
        chat_models = []
        for model, result in results['chat_results'].items():
            if result['success']:
                chat_models.append((model, result['time']))
        
        if chat_models:
            summary['best_chat_model'] = min(chat_models, key=lambda x: x[1])[0]
            summary['working_models'].extend([m[0] for m in chat_models])
        
        # Рекомендации
        if summary['best_sql_model']:
            summary['recommendations'].append(f"Лучшая для SQL: {summary['best_sql_model']}")
        
        if summary['best_chat_model']:
            summary['recommendations'].append(f"Лучшая для чата: {summary['best_chat_model']}")
        
        if not summary['working_models']:
            summary['recommendations'].append("⚠️ Ни одна модель не работает!")
        else:
            summary['recommendations'].append(f"✅ Работающих моделей: {len(set(summary['working_models']))}")
        
        return summary
    
    def _save_quick_results(self, results: Dict[str, Any]):
        """Сохранение быстрых результатов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_agents_test_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
    
    def print_quick_summary(self, results: Dict[str, Any]):
        """Вывод быстрого отчета"""
        print("\n" + "="*50)
        print("📊 БЫСТРЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ")
        print("="*50)
        
        summary = results['summary']
        
        print(f"📅 Дата: {results['test_date']}")
        print(f"🤖 Моделей: {len(results['models_tested'])}")
        
        print(f"\n📊 SQL РЕЗУЛЬТАТЫ:")
        for model, result in results['sql_results'].items():
            status = "✅" if result['success'] else "❌"
            time_str = f"{result['time']:.2f}с" if result['success'] else "Ошибка"
            print(f"  {status} {model}: {time_str}")
        
        print(f"\n💬 ЧАТ РЕЗУЛЬТАТЫ:")
        for model, result in results['chat_results'].items():
            status = "✅" if result['success'] else "❌"
            time_str = f"{result['time']:.2f}с" if result['success'] else "Ошибка"
            print(f"  {status} {model}: {time_str}")
        
        print(f"\n🏆 ЛУЧШИЕ МОДЕЛИ:")
        if summary.get('best_sql_model'):
            print(f"  📊 SQL: {summary['best_sql_model']}")
        if summary.get('best_chat_model'):
            print(f"  💬 Чат: {summary['best_chat_model']}")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in summary.get('recommendations', []):
            print(f"  • {rec}")
        
        print("="*50)

def main():
    """Основная функция"""
    print("⚡ БЫСТРЫЙ ТЕСТ АГЕНТОВ KB ADMIN")
    print("=" * 40)
    print("Тестируем только 2 модели по 1 вопросу каждая")
    print("=" * 40)
    
    try:
        tester = QuickAgentsTester()
        results = tester.run_quick_test()
        tester.print_quick_summary(results)
        
        print(f"\n🎉 Быстрый тест завершен!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тест прерван")
        return 1
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)







