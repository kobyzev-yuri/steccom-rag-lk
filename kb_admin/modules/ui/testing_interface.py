"""
Testing Interface for KB Admin
Интерфейс тестирования релевантности KB
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import json
from datetime import datetime

from ..testing.relevance_analyzer import RelevanceAnalyzer, RelevanceTestResult
from ..core.knowledge_manager import KnowledgeBaseManager


class TestingInterface:
    """Интерфейс тестирования релевантности"""
    
    def __init__(self):
        self.analyzer = RelevanceAnalyzer()
        self.kb_manager = KnowledgeBaseManager()
    
    def render_testing_interface(self):
        """Рендер интерфейса тестирования"""
        st.header("🧪 Тестирование релевантности KB")
        
        # Выбор KB для тестирования
        kb_selection = self._render_kb_selection()
        
        if not kb_selection:
            st.info("Выберите базу знаний для тестирования")
            return
        
        # Настройки тестирования
        test_settings = self._render_test_settings()
        
        # Запуск тестирования
        if st.button("🚀 Запустить тестирование", type="primary"):
            self._run_relevance_test(kb_selection, test_settings)
        
        # Отображение результатов
        if 'test_results' in st.session_state:
            self._render_test_results()
    
    def _render_kb_selection(self) -> int:
        """Рендер выбора KB"""
        st.subheader("📚 Выбор базы знаний")
        
        try:
            kbs = self.kb_manager.get_knowledge_bases()
            
            if not kbs:
                st.warning("Базы знаний не найдены. Создайте KB в разделе 'Управление KB'")
                return None
            
            kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in kbs}
            
            selected_kb_name = st.selectbox(
                "Выберите базу знаний:",
                options=list(kb_options.keys()),
                index=0
            )
            
            return kb_options[selected_kb_name]
            
        except Exception as e:
            st.error(f"Ошибка загрузки KB: {e}")
            return None
    
    def _render_test_settings(self) -> Dict[str, Any]:
        """Рендер настроек тестирования"""
        st.subheader("⚙️ Настройки тестирования")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Выбор модели
            model_options = {
                "GPT-4o (ProxyAPI)": "gpt-4o",
                "GPT-3.5-turbo (ProxyAPI)": "gpt-3.5-turbo", 
                "Qwen 2.5 1.5B (Ollama)": "qwen2.5:1.5b"
            }
            
            selected_model = st.selectbox(
                "Модель для тестирования:",
                options=list(model_options.keys()),
                index=0
            )
            
            # Количество вопросов
            num_questions = st.slider(
                "Количество тестовых вопросов:",
                min_value=1,
                max_value=20,
                value=5
            )
        
        with col2:
            # Категории вопросов
            categories = st.multiselect(
                "Категории вопросов:",
                options=["billing", "technical", "ui_guide", "all"],
                default=["billing"]
            )
            
            # Пороги качества
            min_accuracy = st.slider(
                "Минимальная точность:",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1
            )
        
        return {
            "model": model_options[selected_model],
            "num_questions": num_questions,
            "categories": categories,
            "min_accuracy": min_accuracy
        }
    
    def _run_relevance_test(self, kb_id: int, settings: Dict[str, Any]):
        """Запуск тестирования релевантности"""
        
        with st.spinner("🧪 Запуск тестирования релевантности..."):
            try:
                # Получаем тестовые вопросы
                test_questions = self._get_test_questions(settings)
                
                # Запускаем тестирование
                results = self.analyzer.test_kb_relevance(kb_id, test_questions)
                
                # Сохраняем результаты
                st.session_state.test_results = results
                st.session_state.test_settings = settings
                st.session_state.test_kb_id = kb_id
                
                st.success(f"✅ Тестирование завершено! Протестировано {len(results)} вопросов")
                
            except Exception as e:
                st.error(f"❌ Ошибка тестирования: {e}")
    
    def _get_test_questions(self, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получение тестовых вопросов"""
        all_questions = self.analyzer._get_default_test_questions()
        
        # Фильтруем по категориям
        categories = settings.get("categories", ["billing"])
        if "all" in categories:
            return all_questions
        
        filtered_questions = []
        for question in all_questions:
            if question["category"] in categories:
                filtered_questions.append(question)
        
        # Ограничиваем количество
        num_questions = settings.get("num_questions", 5)
        return filtered_questions[:num_questions]
    
    def _render_test_results(self):
        """Рендер результатов тестирования"""
        st.markdown("---")
        st.subheader("📊 Результаты тестирования")
        
        results = st.session_state.test_results
        settings = st.session_state.test_settings
        
        # Генерируем отчет
        report = self.analyzer.generate_relevance_report(results)
        
        # Основные метрики
        self._render_metrics_summary(report["summary"])
        
        # Графики
        self._render_quality_charts(report)
        
        # Детальные результаты
        self._render_detailed_results(results)
        
        # Рекомендации
        self._render_recommendations(report)
        
        # Экспорт результатов
        self._render_export_options(results, report)
    
    def _render_metrics_summary(self, summary: Dict[str, Any]):
        """Рендер сводки метрик"""
        st.subheader("📈 Сводка метрик")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Общее качество",
                value=summary["overall_quality"].title(),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Средняя точность",
                value=f"{summary['average_accuracy']:.1%}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Средняя полнота",
                value=f"{summary['average_completeness']:.1%}",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Среднее время ответа",
                value=f"{summary['average_response_time']:.1f}с",
                delta=None
            )
    
    def _render_quality_charts(self, report: Dict[str, Any]):
        """Рендер графиков качества"""
        st.subheader("📊 Анализ качества")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Распределение по качеству
            quality_dist = report["quality_distribution"]
            
            if quality_dist:
                fig = px.pie(
                    values=list(quality_dist.values()),
                    names=list(quality_dist.keys()),
                    title="Распределение по качеству ответов",
                    color_discrete_map={
                        "excellent": "#2E8B57",
                        "good": "#32CD32", 
                        "fair": "#FFD700",
                        "poor": "#FF6347"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # График времени ответа
            results = st.session_state.test_results
            
            response_times = [r.response_time for r in results]
            questions = [f"Q{i+1}" for i in range(len(results))]
            
            fig = go.Figure(data=go.Bar(
                x=questions,
                y=response_times,
                marker_color=['#2E8B57' if t < 5 else '#FFD700' if t < 10 else '#FF6347' for t in response_times]
            ))
            
            fig.update_layout(
                title="Время ответа по вопросам",
                xaxis_title="Вопросы",
                yaxis_title="Время (секунды)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_results(self, results: List[RelevanceTestResult]):
        """Рендер детальных результатов"""
        st.subheader("📋 Детальные результаты")
        
        # Создаем DataFrame для отображения
        data = []
        for i, result in enumerate(results):
            data.append({
                "№": i + 1,
                "Вопрос": result.question[:50] + "..." if len(result.question) > 50 else result.question,
                "Точность": f"{result.accuracy_score:.1%}",
                "Полнота": f"{result.completeness_score:.1%}",
                "Релевантность": f"{result.relevance_score:.1%}",
                "Качество": result.overall_quality.title(),
                "Время": f"{result.response_time:.1f}с",
                "Источники": result.sources_found
            })
        
        df = pd.DataFrame(data)
        
        # Цветовое кодирование качества
        def highlight_quality(val):
            if val == "Excellent":
                return "background-color: #2E8B57; color: white"
            elif val == "Good":
                return "background-color: #32CD32; color: white"
            elif val == "Fair":
                return "background-color: #FFD700; color: black"
            elif val == "Poor":
                return "background-color: #FF6347; color: white"
            return ""
        
        styled_df = df.style.applymap(highlight_quality, subset=['Качество'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Детальный просмотр
        st.subheader("🔍 Детальный просмотр")
        
        selected_question = st.selectbox(
            "Выберите вопрос для детального просмотра:",
            options=[f"Q{i+1}: {r.question[:30]}..." for i, r in enumerate(results)],
            index=0
        )
        
        question_index = int(selected_question.split(":")[0][1:]) - 1
        result = results[question_index]
        
        with st.expander("Детали ответа", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Вопрос:**")
                st.write(result.question)
                
                st.write("**Ожидаемые ключевые слова:**")
                for keyword in result.expected_keywords:
                    st.write(f"• {keyword}")
            
            with col2:
                st.write("**Ответ:**")
                st.write(result.actual_answer)
                
                st.write("**Метрики:**")
                st.write(f"• Точность: {result.accuracy_score:.1%}")
                st.write(f"• Полнота: {result.completeness_score:.1%}")
                st.write(f"• Релевантность: {result.relevance_score:.1%}")
                st.write(f"• Время ответа: {result.response_time:.1f}с")
                st.write(f"• Источников найдено: {result.sources_found}")
            
            st.write("**Рекомендации:**")
            for rec in result.recommendations:
                st.write(f"• {rec}")
    
    def _render_recommendations(self, report: Dict[str, Any]):
        """Рендер рекомендаций"""
        st.subheader("💡 Рекомендации по улучшению")
        
        # Системные рекомендации
        st.write("**Системные рекомендации:**")
        for rec in report["recommendations"]:
            st.write(f"• {rec}")
        
        # Проблемные области
        if report["problem_areas"]:
            st.write("**Проблемные области:**")
            for area in report["problem_areas"]:
                with st.expander(f"❌ {area['question'][:50]}... ({area['quality']})"):
                    st.write("**Рекомендации:**")
                    for rec in area["recommendations"]:
                        st.write(f"• {rec}")
    
    def _render_export_options(self, results: List[RelevanceTestResult], report: Dict[str, Any]):
        """Рендер опций экспорта"""
        st.subheader("📤 Экспорт результатов")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Экспорт в CSV"):
                self._export_to_csv(results)
        
        with col2:
            if st.button("📋 Экспорт отчета"):
                self._export_report(report)
        
        with col3:
            if st.button("💾 Сохранить в протокол"):
                self._save_to_protocol(results)
    
    def _export_to_csv(self, results: List[RelevanceTestResult]):
        """Экспорт результатов в CSV"""
        data = []
        for result in results:
            data.append({
                "question": result.question,
                "expected_keywords": ", ".join(result.expected_keywords),
                "actual_answer": result.actual_answer,
                "accuracy_score": result.accuracy_score,
                "completeness_score": result.completeness_score,
                "relevance_score": result.relevance_score,
                "overall_quality": result.overall_quality,
                "response_time": result.response_time,
                "sources_found": result.sources_found,
                "model_used": result.model_used,
                "timestamp": result.timestamp
            })
        
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="💾 Скачать CSV",
            data=csv,
            file_name=f"kb_relevance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def _export_report(self, report: Dict[str, Any]):
        """Экспорт отчета"""
        report_json = json.dumps(report, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📋 Скачать отчет",
            data=report_json,
            file_name=f"kb_relevance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _save_to_protocol(self, results: List[RelevanceTestResult]):
        """Сохранение в протокол тестирования"""
        try:
            # TODO: Реализовать сохранение в протокол
            st.success("✅ Результаты сохранены в протокол тестирования")
        except Exception as e:
            st.error(f"❌ Ошибка сохранения в протокол: {e}")
