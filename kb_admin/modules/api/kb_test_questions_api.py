"""
API для получения тестовых вопросов из БЗ
Используется другими системами (ai_billing, etc.) для тестирования релевантности БЗ
"""

import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..core.knowledge_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb-test-questions", tags=["KB Test Questions"])

class TestQuestion(BaseModel):
    question: str
    expected_keywords: List[str]
    category: str
    difficulty: str

class TestQuestionsResponse(BaseModel):
    kb_id: int
    kb_name: str
    questions: List[TestQuestion]
    created_at: str
    created_by: str
    version: str
    description: str

@router.get("/{kb_id}", response_model=TestQuestionsResponse)
async def get_test_questions(kb_id: int):
    """Получение тестовых вопросов для конкретной БЗ"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb_info = kb_manager.get_knowledge_base(kb_id)
        if not kb_info:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Получаем метаданные с тестовыми вопросами
        metadata = kb_manager.get_knowledge_base_metadata(kb_id, "relevance_test_questions")
        
        if "relevance_test_questions" not in metadata:
            raise HTTPException(status_code=404, detail=f"Для БЗ ID {kb_id} не найдены тестовые вопросы")
        
        # Парсим данные
        test_questions_data = json.loads(metadata["relevance_test_questions"])
        
        # Преобразуем в Pydantic модели
        questions = []
        for q in test_questions_data.get("questions", []):
            questions.append(TestQuestion(
                question=q["question"],
                expected_keywords=q.get("expected_keywords", []),
                category=q.get("category", "general"),
                difficulty=q.get("difficulty", "medium")
            ))
        
        return TestQuestionsResponse(
            kb_id=kb_id,
            kb_name=kb_info["name"],
            questions=questions,
            created_at=test_questions_data.get("created_at", ""),
            created_by=test_questions_data.get("created_by", ""),
            version=test_questions_data.get("version", "1.0"),
            description=test_questions_data.get("description", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения тестовых вопросов для БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_kbs_with_test_questions():
    """Получение списка БЗ с тестовыми вопросами"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Получаем все активные БЗ
        kbs = kb_manager.get_knowledge_bases(active_only=True)
        
        result = []
        for kb in kbs:
            # Проверяем наличие тестовых вопросов
            metadata = kb_manager.get_knowledge_base_metadata(kb["id"], "relevance_test_questions")
            
            if "relevance_test_questions" in metadata:
                test_questions_data = json.loads(metadata["relevance_test_questions"])
                questions_count = len(test_questions_data.get("questions", []))
                
                result.append({
                    "kb_id": kb["id"],
                    "kb_name": kb["name"],
                    "category": kb["category"],
                    "questions_count": questions_count,
                    "created_at": test_questions_data.get("created_at", ""),
                    "created_by": test_questions_data.get("created_by", "")
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения списка БЗ с тестовыми вопросами: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/{kb_id}/test")
async def test_kb_relevance(
    kb_id: int,
    question: str = Query(..., description="Вопрос для тестирования"),
    expected_keywords: Optional[str] = Query(None, description="Ожидаемые ключевые слова через запятую")
):
    """Быстрое тестирование релевантности БЗ по одному вопросу"""
    try:
        from ..rag.multi_kb_rag import MultiKBRAG
        import time
        
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb_info = kb_manager.get_knowledge_base(kb_id)
        if not kb_info:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Инициализируем RAG систему
        rag = MultiKBRAG()
        rag.load_all_active_kbs()
        
        # Выполняем поиск
        start_time = time.time()
        search_result = rag.ask_question(question)
        response_time = time.time() - start_time
        
        answer = search_result.get("answer", "")
        sources = search_result.get("sources", [])
        
        # Фильтруем источники только по нашей БЗ
        kb_sources = [s for s in sources if s.get('kb_id') == kb_id]
        
        # Анализируем релевантность если указаны ключевые слова
        relevance_score = None
        found_keywords = []
        missing_keywords = []
        
        if expected_keywords:
            keywords_list = [k.strip() for k in expected_keywords.split(",")]
            found_keywords = [k for k in keywords_list if k.lower() in answer.lower()]
            missing_keywords = [k for k in keywords_list if k.lower() not in answer.lower()]
            relevance_score = (len(found_keywords) / len(keywords_list)) * 100 if keywords_list else 0
        
        return {
            "kb_id": kb_id,
            "kb_name": kb_info["name"],
            "question": question,
            "answer": answer,
            "response_time": response_time,
            "sources_found": len(kb_sources),
            "relevance_score": relevance_score,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "sources": kb_sources[:3]  # Возвращаем только первые 3 источника
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка тестирования БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
