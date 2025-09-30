"""
Agent Statistics Panel
Панель статистики агентов
"""

import streamlit as st
import pandas as pd
import sqlite3
from typing import Dict, List, Any
from pathlib import Path
import sys

# Добавляем путь к конфигурации
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import DATABASE_PATH

class AgentStatsPanel:
    """Панель для отображения статистики агентов"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    def render_agent_stats(self):
        """Отобразить статистику агентов"""
        st.subheader("🤖 Статистика агентов")
        
        try:
            # Общая статистика по агентам
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Проверяем существование таблицы
            c.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    agent_name TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    question TEXT,
                    response_length INTEGER
                )
            """)
            
            # Статистика по агентам
            c.execute("""
                SELECT 
                    COALESCE(agent_name, 'unknown') as agent,
                    COUNT(*) as requests,
                    COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                    COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                    COALESCE(SUM(total_tokens), 0) as total_tokens
                FROM llm_usage
                GROUP BY agent_name
                ORDER BY total_tokens DESC
            """)
            
            agent_stats = c.fetchall()
            
            if agent_stats:
                # Создаем DataFrame
                df_agents = pd.DataFrame(agent_stats, columns=[
                    'Агент', 'Запросов', 'Промпт токены', 'Ответ токены', 'Всего токенов'
                ])
                
                # Отображаем общую статистику
                col1, col2, col3, col4 = st.columns(4)
                
                total_requests = df_agents['Запросов'].sum()
                total_tokens = df_agents['Всего токенов'].sum()
                total_agents = len(df_agents)
                avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
                
                with col1:
                    st.metric("Всего агентов", total_agents)
                with col2:
                    st.metric("Всего запросов", total_requests)
                with col3:
                    st.metric("Всего токенов", f"{total_tokens:,}")
                with col4:
                    st.metric("Среднее токенов/запрос", f"{avg_tokens_per_request:.1f}")
                
                st.markdown("---")
                
                # Таблица агентов
                st.markdown("**📊 Статистика по агентам:**")
                st.dataframe(df_agents, use_container_width=True)
                
                # График использования
                if len(df_agents) > 1:
                    st.markdown("**📈 График использования токенов:**")
                    chart_data = df_agents.set_index('Агент')['Всего токенов']
                    st.bar_chart(chart_data)
                
            else:
                st.info("Пока нет данных по использованию агентов")
            
            # Детальная статистика по моделям
            st.markdown("---")
            st.markdown("**🔍 Детальная статистика по моделям:**")
            
            c.execute("""
                SELECT 
                    COALESCE(agent_name, 'unknown') as agent,
                    COALESCE(model, 'unknown') as model,
                    COALESCE(provider, 'unknown') as provider,
                    COUNT(*) as requests,
                    COALESCE(SUM(total_tokens), 0) as total_tokens
                FROM llm_usage
                GROUP BY agent_name, model, provider
                ORDER BY total_tokens DESC
            """)
            
            model_stats = c.fetchall()
            
            if model_stats:
                df_models = pd.DataFrame(model_stats, columns=[
                    'Агент', 'Модель', 'Провайдер', 'Запросов', 'Токенов'
                ])
                st.dataframe(df_models, use_container_width=True)
            
            # Последние операции
            st.markdown("---")
            st.markdown("**⏰ Последние операции (20):**")
            
            c.execute("""
                SELECT 
                    timestamp,
                    COALESCE(agent_name, 'unknown') as agent,
                    COALESCE(model, 'unknown') as model,
                    COALESCE(total_tokens, 0) as tokens,
                    LENGTH(question) as question_length
                FROM llm_usage
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            
            recent_ops = c.fetchall()
            
            if recent_ops:
                df_recent = pd.DataFrame(recent_ops, columns=[
                    'Время', 'Агент', 'Модель', 'Токенов', 'Длина вопроса'
                ])
                st.dataframe(df_recent, use_container_width=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Ошибка получения статистики агентов: {e}")
    
    def get_agent_leaderboard(self) -> List[Dict[str, Any]]:
        """Получить рейтинг агентов по использованию токенов"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                SELECT 
                    COALESCE(agent_name, 'unknown') as agent,
                    COUNT(*) as requests,
                    COALESCE(SUM(total_tokens), 0) as total_tokens,
                    COALESCE(AVG(total_tokens), 0) as avg_tokens_per_request
                FROM llm_usage
                GROUP BY agent_name
                ORDER BY total_tokens DESC
                LIMIT 10
            """)
            
            leaderboard = []
            for row in c.fetchall():
                leaderboard.append({
                    'agent': row[0],
                    'requests': row[1],
                    'total_tokens': row[2],
                    'avg_tokens_per_request': row[3]
                })
            
            conn.close()
            return leaderboard
            
        except Exception as e:
            st.error(f"Ошибка получения рейтинга: {e}")
            return []
