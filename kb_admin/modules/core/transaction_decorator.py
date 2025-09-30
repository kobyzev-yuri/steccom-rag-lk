"""
Transaction Decorator - Декоратор для автоматического управления транзакциями
"""

import functools
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

def with_transaction(operation_type: str, auto_commit: bool = True):
    """
    Декоратор для автоматического управления транзакциями
    
    Args:
        operation_type: Тип операции (например, 'document_analysis', 'kb_creation')
        auto_commit: Автоматически подтверждать транзакцию при успешном выполнении
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем transaction_manager из первого аргумента (self)
            transaction_manager = None
            if args and hasattr(args[0], 'transaction_manager'):
                transaction_manager = args[0].transaction_manager
            elif 'transaction_manager' in kwargs:
                transaction_manager = kwargs['transaction_manager']
            
            if not transaction_manager:
                logger.warning("TransactionManager не найден, выполнение без транзакции")
                return func(*args, **kwargs)
            
            # Начинаем транзакцию
            transaction_id = transaction_manager.begin_transaction(
                operation_type=operation_type,
                metadata={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
            )
            
            try:
                # Выполняем функцию с transaction_id в kwargs
                kwargs['transaction_id'] = transaction_id
                result = func(*args, **kwargs)
                
                if auto_commit:
                    # Автоматически подтверждаем транзакцию
                    success = transaction_manager.commit_transaction(transaction_id)
                    if success:
                        logger.info(f"Транзакция {transaction_id} автоматически подтверждена")
                    else:
                        logger.error(f"Ошибка подтверждения транзакции {transaction_id}")
                        # Пытаемся откатить
                        transaction_manager.rollback_transaction(transaction_id)
                        raise Exception("Ошибка подтверждения транзакции")
                
                return result
                
            except Exception as e:
                # Откатываем транзакцию при ошибке
                logger.error(f"Ошибка в транзакции {transaction_id}: {e}")
                try:
                    rollback_success = transaction_manager.rollback_transaction(transaction_id)
                    if rollback_success:
                        logger.info(f"Транзакция {transaction_id} успешно откачена")
                    else:
                        logger.error(f"Ошибка отката транзакции {transaction_id}")
                except Exception as rollback_error:
                    logger.error(f"Критическая ошибка отката транзакции {transaction_id}: {rollback_error}")
                
                raise e
        
        return wrapper
    return decorator

def manual_transaction(operation_type: str):
    """
    Декоратор для ручного управления транзакциями
    Транзакция не подтверждается автоматически, нужно вызывать commit/rollback вручную
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем transaction_manager из первого аргумента (self)
            transaction_manager = None
            if args and hasattr(args[0], 'transaction_manager'):
                transaction_manager = args[0].transaction_manager
            elif 'transaction_manager' in kwargs:
                transaction_manager = kwargs['transaction_manager']
            
            if not transaction_manager:
                logger.warning("TransactionManager не найден, выполнение без транзакции")
                return func(*args, **kwargs)
            
            # Начинаем транзакцию
            transaction_id = transaction_manager.begin_transaction(
                operation_type=operation_type,
                metadata={
                    'function': func.__name__,
                    'manual_mode': True
                }
            )
            
            try:
                # Выполняем функцию с transaction_id в kwargs
                kwargs['transaction_id'] = transaction_id
                result = func(*args, **kwargs)
                
                # Возвращаем результат вместе с transaction_id для ручного управления
                if isinstance(result, dict):
                    result['transaction_id'] = transaction_id
                else:
                    # Если результат не dict, создаем обертку
                    result = {
                        'data': result,
                        'transaction_id': transaction_id
                    }
                
                return result
                
            except Exception as e:
                # Откатываем транзакцию при ошибке
                logger.error(f"Ошибка в транзакции {transaction_id}: {e}")
                try:
                    transaction_manager.rollback_transaction(transaction_id)
                except Exception as rollback_error:
                    logger.error(f"Критическая ошибка отката транзакции {transaction_id}: {rollback_error}")
                
                raise e
        
        return wrapper
    return decorator
