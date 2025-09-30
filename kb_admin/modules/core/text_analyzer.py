"""
Text Structure Analyzer
Анализатор структуры текста для оптимизации разбиения на чанки
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextStructure:
    """Структура текста"""
    total_length: int
    paragraph_count: int
    section_count: int
    average_paragraph_length: float
    has_numbered_sections: bool
    has_bullet_points: bool
    language: str
    complexity_score: float
    recommended_chunk_size: int
    recommended_overlap: int


class TextAnalyzer:
    """Анализатор структуры текста"""
    
    def __init__(self):
        self.section_patterns = [
            r'^\d+\.\s+',  # 1. Заголовок
            r'^\d+\.\d+\s+',  # 1.1 Подзаголовок
            r'^[IVX]+\.\s+',  # I. Римские цифры
            r'^[А-Я][а-я]+\s+\d+\.',  # Раздел 1.
            r'^Глава\s+\d+',  # Глава 1
            r'^Часть\s+\d+',  # Часть 1
        ]

    # Заглушки для совместимости с менеджером моделей UI
    def get_chat_backend_info(self) -> Dict[str, Any]:
        """Возвращает пустую конфигурацию, т.к. не использует LLM напрямую."""
        return {"provider": "n/a", "model": "n/a"}

    def set_chat_backend(self, provider: str, model: str, **kwargs) -> None:
        """Игнорируем, т.к. модуль не использует LLM напрямую."""
        return
        
        self.bullet_patterns = [
            r'^[-•*]\s+',  # - пункт
            r'^\d+\)\s+',  # 1) пункт
            r'^[а-я]\)\s+',  # а) пункт
        ]
    
    def analyze_text_structure(self, text: str) -> TextStructure:
        """Анализ структуры текста"""
        if not text or not text.strip():
            return self._get_default_structure()
        
        # Основные метрики
        total_length = len(text)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Анализ секций
        sections = self._find_sections(text)
        section_count = len(sections)
        has_numbered_sections = section_count > 0
        
        # Анализ списков
        has_bullet_points = self._has_bullet_points(text)
        
        # Средняя длина параграфа
        if paragraph_count > 0:
            avg_paragraph_length = sum(len(p) for p in paragraphs) / paragraph_count
        else:
            avg_paragraph_length = 0
        
        # Определение языка
        language = self._detect_language(text)
        
        # Оценка сложности
        complexity_score = self._calculate_complexity(text, paragraphs, sections)
        
        # Рекомендации по чанкам
        recommended_chunk_size, recommended_overlap = self._recommend_chunk_settings(
            total_length, paragraph_count, section_count, avg_paragraph_length, complexity_score
        )
        
        return TextStructure(
            total_length=total_length,
            paragraph_count=paragraph_count,
            section_count=section_count,
            average_paragraph_length=avg_paragraph_length,
            has_numbered_sections=has_numbered_sections,
            has_bullet_points=has_bullet_points,
            language=language,
            complexity_score=complexity_score,
            recommended_chunk_size=recommended_chunk_size,
            recommended_overlap=recommended_overlap
        )
    
    def _find_sections(self, text: str) -> List[Tuple[int, str]]:
        """Поиск секций в тексте"""
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in self.section_patterns:
                if re.match(pattern, line):
                    sections.append((i, line))
                    break
        
        return sections
    
    def _has_bullet_points(self, text: str) -> bool:
        """Проверка наличия списков"""
        lines = text.split('\n')
        bullet_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in self.bullet_patterns:
                if re.match(pattern, line):
                    bullet_count += 1
                    break
        
        return bullet_count > 2  # Если больше 2 пунктов, считаем что есть список
    
    def _detect_language(self, text: str) -> str:
        """Определение языка текста"""
        # Простая эвристика для русского/английского
        cyrillic_chars = len(re.findall(r'[а-яё]', text.lower()))
        latin_chars = len(re.findall(r'[a-z]', text.lower()))
        
        if cyrillic_chars > latin_chars:
            return 'ru'
        elif latin_chars > cyrillic_chars:
            return 'en'
        else:
            return 'mixed'
    
    def _calculate_complexity(self, text: str, paragraphs: List[str], sections: List[Tuple[int, str]]) -> float:
        """Расчет сложности текста (0.0 - 1.0)"""
        complexity = 0.0
        
        # Фактор длины
        if len(text) > 10000:
            complexity += 0.3
        elif len(text) > 5000:
            complexity += 0.2
        elif len(text) > 1000:
            complexity += 0.1
        
        # Фактор количества параграфов
        if len(paragraphs) > 20:
            complexity += 0.2
        elif len(paragraphs) > 10:
            complexity += 0.1
        
        # Фактор структурированности
        if len(sections) > 5:
            complexity += 0.2
        elif len(sections) > 2:
            complexity += 0.1
        
        # Фактор технических терминов
        technical_terms = len(re.findall(r'\b(?:API|SQL|HTTP|TCP|IP|JSON|XML|PDF|DOC|XLS)\b', text, re.IGNORECASE))
        if technical_terms > 10:
            complexity += 0.2
        elif technical_terms > 5:
            complexity += 0.1
        
        return min(1.0, complexity)
    
    def _recommend_chunk_settings(self, total_length: int, paragraph_count: int, 
                                section_count: int, avg_paragraph_length: float, 
                                complexity_score: float) -> Tuple[int, int]:
        """Рекомендации по настройкам чанков"""
        
        # Базовые настройки
        base_chunk_size = 600
        base_overlap = 100
        
        # Корректировка на основе структуры
        if section_count > 0:
            # Если есть секции, делаем чанки меньше для сохранения контекста
            base_chunk_size = 500
            base_overlap = 120
        elif avg_paragraph_length > 1000:
            # Если параграфы длинные, увеличиваем чанки
            base_chunk_size = 800
            base_overlap = 150
        elif avg_paragraph_length < 200:
            # Если параграфы короткие, уменьшаем чанки
            base_chunk_size = 400
            base_overlap = 80
        
        # Корректировка на основе сложности
        if complexity_score > 0.7:
            # Сложный текст - больше перекрытие
            base_overlap = int(base_overlap * 1.5)
        elif complexity_score < 0.3:
            # Простой текст - меньше перекрытие
            base_overlap = int(base_overlap * 0.7)
        
        # Корректировка на основе общего размера
        if total_length > 50000:
            # Большой документ - больше чанки
            base_chunk_size = int(base_chunk_size * 1.2)
        elif total_length < 5000:
            # Маленький документ - меньше чанки
            base_chunk_size = int(base_chunk_size * 0.8)
        
        return base_chunk_size, base_overlap
    
    def _get_default_structure(self) -> TextStructure:
        """Структура по умолчанию для пустого текста"""
        return TextStructure(
            total_length=0,
            paragraph_count=0,
            section_count=0,
            average_paragraph_length=0.0,
            has_numbered_sections=False,
            has_bullet_points=False,
            language='unknown',
            complexity_score=0.0,
            recommended_chunk_size=600,
            recommended_overlap=100
        )
    
    def get_analysis_summary(self, structure: TextStructure) -> str:
        """Получение текстового описания анализа"""
        summary = f"""
📊 Анализ структуры текста:
• Общая длина: {structure.total_length:,} символов
• Параграфов: {structure.paragraph_count}
• Секций: {structure.section_count}
• Средняя длина параграфа: {structure.average_paragraph_length:.0f} символов
• Язык: {structure.language}
• Сложность: {structure.complexity_score:.2f}/1.0

🎯 Рекомендации:
• Размер чанка: {structure.recommended_chunk_size}
• Перекрытие: {structure.recommended_overlap}
• Структурированность: {'Высокая' if structure.has_numbered_sections else 'Низкая'}
• Списки: {'Есть' if structure.has_bullet_points else 'Нет'}
        """
        return summary.strip()
