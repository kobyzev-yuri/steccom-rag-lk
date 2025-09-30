"""
Chunk Optimization Module
Модуль оптимизации разбиения текста на чанки
"""

import re
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from .text_analyzer import TextAnalyzer, TextStructure


@dataclass
class ChunkConfig:
    """Конфигурация разбиения на чанки"""
    chunk_size: int
    chunk_overlap: int
    separators: List[str]
    length_function: str = "len"
    description: str = ""
    use_case: str = ""


@dataclass
class ChunkResult:
    """Результат разбиения на чанки"""
    chunks: List[Document]
    config: ChunkConfig
    metrics: Dict[str, Any]
    quality_score: float


class ChunkOptimizer:
    """Оптимизатор разбиения на чанки"""
    
    def __init__(self):
        self.text_analyzer = TextAnalyzer()
        
        # Предустановленные конфигурации
        self.preset_configs = {
            "regulations": ChunkConfig(
                chunk_size=600,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
                description="Регламенты и техническая документация",
                use_case="technical_docs"
            ),
            "manuals": ChunkConfig(
                chunk_size=800,
                chunk_overlap=150,
                separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
                description="Руководства пользователя",
                use_case="user_manuals"
            ),
            "faq": ChunkConfig(
                chunk_size=400,
                chunk_overlap=80,
                separators=["\n\n", "\n", "? ", ". ", " ", ""],
                description="Часто задаваемые вопросы",
                use_case="faq_docs"
            ),
            "api_docs": ChunkConfig(
                chunk_size=700,
                chunk_overlap=120,
                separators=["\n\n", "\n", "```", "## ", "# ", ". ", " ", ""],
                description="Документация API",
                use_case="api_documentation"
            ),
            "legal": ChunkConfig(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", "Статья ", "Пункт ", ". ", " ", ""],
                description="Правовые документы",
                use_case="legal_documents"
            )
        }

    # Заглушки для совместимости с менеджером моделей UI
    def get_chat_backend_info(self) -> Dict[str, Any]:
        """Возвращает пустую конфигурацию, т.к. не использует LLM напрямую."""
        return {"provider": "n/a", "model": "n/a"}

    def set_chat_backend(self, provider: str, model: str, **kwargs) -> None:
        """Игнорируем, т.к. модуль не использует LLM напрямую."""
        return
    
    def optimize_chunking(self, text: str, document_type: str = "auto") -> ChunkResult:
        """Оптимизация разбиения на чанки"""
        
        # Анализ структуры текста
        structure = self.text_analyzer.analyze_text_structure(text)
        
        # Выбор конфигурации
        if document_type == "auto":
            config = self._auto_select_config(structure)
        elif document_type in self.preset_configs:
            config = self.preset_configs[document_type]
        else:
            config = self._create_custom_config(structure)
        
        # Разбиение на чанки
        chunks = self._split_text(text, config)
        
        # Анализ качества
        metrics = self._analyze_chunk_quality(chunks, structure)
        quality_score = self._calculate_quality_score(metrics, structure)
        
        return ChunkResult(
            chunks=chunks,
            config=config,
            metrics=metrics,
            quality_score=quality_score
        )
    
    def compare_configurations(self, text: str, configs: List[str] = None) -> Dict[str, ChunkResult]:
        """Сравнение различных конфигураций разбиения"""
        if configs is None:
            configs = list(self.preset_configs.keys())
        
        results = {}
        
        for config_name in configs:
            if config_name in self.preset_configs:
                config = self.preset_configs[config_name]
                chunks = self._split_text(text, config)
                metrics = self._analyze_chunk_quality(chunks, self.text_analyzer.analyze_text_structure(text))
                quality_score = self._calculate_quality_score(metrics, self.text_analyzer.analyze_text_structure(text))
                
                results[config_name] = ChunkResult(
                    chunks=chunks,
                    config=config,
                    metrics=metrics,
                    quality_score=quality_score
                )
        
        return results
    
    def _auto_select_config(self, structure: TextStructure) -> ChunkConfig:
        """Автоматический выбор конфигурации на основе анализа"""
        
        # Логика выбора на основе структуры
        if structure.has_numbered_sections and structure.complexity_score > 0.6:
            return self.preset_configs["regulations"]
        elif structure.average_paragraph_length < 300 and structure.paragraph_count > 10:
            return self.preset_configs["faq"]
        elif structure.total_length > 20000 and structure.complexity_score > 0.5:
            return self.preset_configs["legal"]
        elif "API" in structure or "http" in structure.lower():
            return self.preset_configs["api_docs"]
        else:
            return self.preset_configs["manuals"]
    
    def _create_custom_config(self, structure: TextStructure) -> ChunkConfig:
        """Создание пользовательской конфигурации"""
        return ChunkConfig(
            chunk_size=structure.recommended_chunk_size,
            chunk_overlap=structure.recommended_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function="len",
            description="Пользовательская конфигурация",
            use_case="custom"
        )
    
    def _split_text(self, text: str, config: ChunkConfig) -> List[Document]:
        """Разбиение текста на чанки"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
            separators=config.separators
        )
        
        # Создаем документ
        doc = Document(page_content=text, metadata={"source": "text_analysis"})
        
        # Разбиваем на чанки
        chunks = splitter.split_documents([doc])
        
        return chunks
    
    def _analyze_chunk_quality(self, chunks: List[Document], structure: TextStructure) -> Dict[str, Any]:
        """Анализ качества чанков"""
        if not chunks:
            return {"error": "No chunks created"}
        
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        
        metrics = {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "size_variance": self._calculate_variance(chunk_sizes),
            "coverage_ratio": sum(chunk_sizes) / structure.total_length if structure.total_length > 0 else 0,
            "overlap_efficiency": self._calculate_overlap_efficiency(chunks),
            "context_preservation": self._calculate_context_preservation(chunks, structure)
        }
        
        return metrics
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Расчет дисперсии"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _calculate_overlap_efficiency(self, chunks: List[Document]) -> float:
        """Расчет эффективности перекрытия"""
        if len(chunks) < 2:
            return 1.0
        
        # Простая метрика: чем меньше разброс размеров, тем лучше
        sizes = [len(chunk.page_content) for chunk in chunks]
        avg_size = sum(sizes) / len(sizes)
        variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
        
        # Нормализуем к 0-1 (чем меньше дисперсия, тем лучше)
        max_variance = avg_size ** 2  # Максимально возможная дисперсия
        efficiency = 1.0 - (variance / max_variance) if max_variance > 0 else 1.0
        
        return max(0.0, min(1.0, efficiency))
    
    def _calculate_context_preservation(self, chunks: List[Document], structure: TextStructure) -> float:
        """Расчет сохранения контекста"""
        if not chunks:
            return 0.0
        
        # Проверяем, сохраняются ли границы секций
        preserved_sections = 0
        total_sections = structure.section_count
        
        if total_sections == 0:
            return 1.0  # Если нет секций, контекст сохраняется полностью
        
        for chunk in chunks:
            content = chunk.page_content
            # Проверяем, содержит ли чанк начало секции
            for pattern in self.text_analyzer.section_patterns:
                if re.search(pattern, content):
                    preserved_sections += 1
                    break
        
        return preserved_sections / total_sections if total_sections > 0 else 1.0
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], structure: TextStructure) -> float:
        """Расчет общего балла качества"""
        if "error" in metrics:
            return 0.0
        
        # Веса для разных метрик
        weights = {
            "coverage_ratio": 0.3,      # Покрытие текста
            "overlap_efficiency": 0.25,  # Эффективность перекрытия
            "context_preservation": 0.25, # Сохранение контекста
            "size_consistency": 0.2      # Консистентность размеров
        }
        
        # Нормализация метрик
        coverage_score = min(1.0, metrics["coverage_ratio"])
        overlap_score = metrics["overlap_efficiency"]
        context_score = metrics["context_preservation"]
        
        # Консистентность размеров (обратная дисперсии)
        size_consistency = 1.0 - (metrics["size_variance"] / (metrics["avg_chunk_size"] ** 2))
        size_consistency = max(0.0, min(1.0, size_consistency))
        
        # Взвешенная сумма
        quality_score = (
            weights["coverage_ratio"] * coverage_score +
            weights["overlap_efficiency"] * overlap_score +
            weights["context_preservation"] * context_score +
            weights["size_consistency"] * size_consistency
        )
        
        return quality_score
    
    def get_optimization_recommendations(self, result: ChunkResult) -> List[str]:
        """Получение рекомендаций по оптимизации"""
        recommendations = []
        
        metrics = result.metrics
        quality_score = result.quality_score
        
        if quality_score < 0.6:
            recommendations.append("⚠️ Низкое качество разбиения. Рекомендуется изменить параметры.")
        
        if metrics["coverage_ratio"] < 0.9:
            recommendations.append("📄 Неполное покрытие текста. Увеличьте размер чанков или перекрытие.")
        
        if metrics["overlap_efficiency"] < 0.7:
            recommendations.append("🔄 Низкая эффективность перекрытия. Оптимизируйте размер перекрытия.")
        
        if metrics["context_preservation"] < 0.8:
            recommendations.append("🔗 Плохое сохранение контекста. Измените разделители или размер чанков.")
        
        if metrics["size_variance"] > metrics["avg_chunk_size"] * 0.5:
            recommendations.append("📏 Большой разброс размеров чанков. Улучшите разделители.")
        
        if not recommendations:
            recommendations.append("✅ Качество разбиения хорошее!")
        
        return recommendations
