"""
API для управления базами знаний
Полный CRUD API для работы с БЗ, документами и метаданными
"""

import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime

from ..core.knowledge_manager import KnowledgeBaseManager
from ..core.smart_document_agent import SmartLibrarian
from ..documents.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb-management", tags=["KB Management"])

# Pydantic models
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str
    category: str
    created_by: str

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    created_at: str
    updated_at: str
    is_active: bool
    created_by: str
    document_count: int = 0

class DocumentResponse(BaseModel):
    id: int
    kb_id: int
    title: str
    file_path: Optional[str]
    content_type: str
    file_size: Optional[int]
    upload_date: str
    processed: bool
    metadata: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    document_id: int
    title: str
    file_path: str
    processed: bool
    analysis: Optional[Dict[str, Any]] = None

class MetadataUpdate(BaseModel):
    metadata_key: str
    metadata_value: str

# Knowledge Base CRUD operations
@router.get("/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases(active_only: bool = Query(True, description="Показать только активные БЗ")):
    """Получение списка баз знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        kbs = kb_manager.get_knowledge_bases(active_only=active_only)
        
        result = []
        for kb in kbs:
            # Получаем количество документов
            documents = kb_manager.get_knowledge_base_documents(kb['id'])
            document_count = len(documents) if documents else 0
            
            result.append(KnowledgeBaseResponse(
                id=kb['id'],
                name=kb['name'],
                description=kb['description'],
                category=kb['category'],
                created_at=kb['created_at'],
                updated_at=kb['updated_at'],
                is_active=kb['is_active'],
                created_by=kb['created_by'],
                document_count=document_count
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения списка БЗ: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: int):
    """Получение конкретной базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        kb = kb_manager.get_knowledge_base(kb_id)
        
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Получаем количество документов
        documents = kb_manager.get_knowledge_base_documents(kb_id)
        document_count = len(documents) if documents else 0
        
        return KnowledgeBaseResponse(
            id=kb['id'],
            name=kb['name'],
            description=kb['description'],
            category=kb['category'],
            created_at=kb['created_at'],
            updated_at=kb['updated_at'],
            is_active=kb['is_active'],
            created_by=kb['created_by'],
            document_count=document_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(kb_data: KnowledgeBaseCreate):
    """Создание новой базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        kb_id = kb_manager.create_knowledge_base(
            name=kb_data.name,
            description=kb_data.description,
            category=kb_data.category,
            created_by=kb_data.created_by
        )
        
        # Получаем созданную БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        
        return KnowledgeBaseResponse(
            id=kb['id'],
            name=kb['name'],
            description=kb['description'],
            category=kb['category'],
            created_at=kb['created_at'],
            updated_at=kb['updated_at'],
            is_active=kb['is_active'],
            created_by=kb['created_by'],
            document_count=0
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания БЗ: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.put("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(kb_id: int, kb_data: KnowledgeBaseUpdate):
    """Обновление базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Обновляем БЗ
        success = kb_manager.update_knowledge_base(
            kb_id=kb_id,
            name=kb_data.name,
            description=kb_data.description,
            category=kb_data.category,
            is_active=kb_data.is_active
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Ошибка обновления БЗ")
        
        # Получаем обновленную БЗ
        updated_kb = kb_manager.get_knowledge_base(kb_id)
        documents = kb_manager.get_knowledge_base_documents(kb_id)
        document_count = len(documents) if documents else 0
        
        return KnowledgeBaseResponse(
            id=updated_kb['id'],
            name=updated_kb['name'],
            description=updated_kb['description'],
            category=updated_kb['category'],
            created_at=updated_kb['created_at'],
            updated_at=updated_kb['updated_at'],
            is_active=updated_kb['is_active'],
            created_by=updated_kb['created_by'],
            document_count=document_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: int):
    """Удаление базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Удаляем БЗ
        success = kb_manager.delete_knowledge_base(kb_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Ошибка удаления БЗ")
        
        return {"message": f"БЗ ID {kb_id} успешно удалена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# Document management
@router.get("/knowledge-bases/{kb_id}/documents", response_model=List[DocumentResponse])
async def get_knowledge_base_documents(kb_id: int):
    """Получение документов базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        documents = kb_manager.get_knowledge_base_documents(kb_id)
        
        result = []
        for doc in documents:
            result.append(DocumentResponse(
                id=doc['id'],
                kb_id=doc['kb_id'],
                title=doc['title'],
                file_path=doc.get('file_path'),
                content_type=doc['content_type'],
                file_size=doc.get('file_size'),
                upload_date=doc['upload_date'],
                processed=doc['processed'],
                metadata=json.loads(doc['metadata']) if doc.get('metadata') else None
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения документов БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/knowledge-bases/{kb_id}/documents", response_model=DocumentUploadResponse)
async def upload_document_to_kb(
    kb_id: int,
    file: UploadFile = File(...),
    created_by: str = Form(...)
):
    """Загрузка документа в базу знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        pdf_processor = PDFProcessor()
        smart_librarian = SmartLibrarian(kb_manager, pdf_processor)
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Сохраняем файл
        from pathlib import Path
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Анализируем документ
        analysis = smart_librarian.analyze_document(file_path)
        
        # Добавляем документ в БЗ
        doc_id = kb_manager.add_document_to_kb(
            kb_id=kb_id,
            title=file.filename,
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            created_by=created_by,
            metadata=json.dumps(analysis, ensure_ascii=False) if analysis else None
        )
        
        return DocumentUploadResponse(
            document_id=doc_id,
            title=file.filename,
            file_path=str(file_path),
            processed=analysis is not None,
            analysis=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки документа в БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# Metadata management
@router.get("/knowledge-bases/{kb_id}/metadata")
async def get_knowledge_base_metadata(
    kb_id: int,
    metadata_key: Optional[str] = Query(None, description="Конкретный ключ метаданных")
):
    """Получение метаданных базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        metadata = kb_manager.get_knowledge_base_metadata(kb_id, metadata_key)
        
        # Парсим JSON значения
        parsed_metadata = {}
        for key, value in metadata.items():
            try:
                parsed_metadata[key] = json.loads(value)
            except json.JSONDecodeError:
                parsed_metadata[key] = value
        
        return {
            "kb_id": kb_id,
            "kb_name": kb['name'],
            "metadata": parsed_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения метаданных БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/knowledge-bases/{kb_id}/metadata")
async def update_knowledge_base_metadata(kb_id: int, metadata_data: MetadataUpdate):
    """Обновление метаданных базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Обновляем метаданные
        success = kb_manager.update_knowledge_base_metadata(
            kb_id=kb_id,
            metadata_key=metadata_data.metadata_key,
            metadata_value=metadata_data.metadata_value
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Ошибка обновления метаданных")
        
        return {
            "message": f"Метаданные '{metadata_data.metadata_key}' успешно обновлены для БЗ ID {kb_id}",
            "kb_id": kb_id,
            "metadata_key": metadata_data.metadata_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления метаданных БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

# Statistics and analytics
@router.get("/knowledge-bases/{kb_id}/stats")
async def get_knowledge_base_stats(kb_id: int):
    """Получение статистики базы знаний"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Проверяем существование БЗ
        kb = kb_manager.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"БЗ с ID {kb_id} не найдена")
        
        # Получаем документы
        documents = kb_manager.get_knowledge_base_documents(kb_id)
        
        # Получаем метаданные
        metadata = kb_manager.get_knowledge_base_metadata(kb_id)
        
        # Подсчитываем статистику
        total_documents = len(documents)
        processed_documents = len([d for d in documents if d['processed']])
        total_size = sum(d.get('file_size', 0) for d in documents if d.get('file_size'))
        
        # Анализируем типы контента
        content_types = {}
        for doc in documents:
            content_type = doc['content_type']
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Проверяем наличие тестовых вопросов
        has_test_questions = "relevance_test_questions" in metadata
        
        return {
            "kb_id": kb_id,
            "kb_name": kb['name'],
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "processing_rate": (processed_documents / total_documents * 100) if total_documents > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "content_types": content_types,
            "has_test_questions": has_test_questions,
            "metadata_keys": list(metadata.keys()),
            "created_at": kb['created_at'],
            "updated_at": kb['updated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статистики БЗ {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("/stats/overview")
async def get_system_overview():
    """Получение общей статистики системы"""
    try:
        kb_manager = KnowledgeBaseManager()
        
        # Получаем все БЗ
        all_kbs = kb_manager.get_knowledge_bases(active_only=False)
        active_kbs = kb_manager.get_knowledge_bases(active_only=True)
        
        # Подсчитываем общую статистику
        total_kbs = len(all_kbs)
        active_kbs_count = len(active_kbs)
        
        total_documents = 0
        total_processed = 0
        total_size = 0
        categories = {}
        
        for kb in all_kbs:
            documents = kb_manager.get_knowledge_base_documents(kb['id'])
            total_documents += len(documents)
            total_processed += len([d for d in documents if d['processed']])
            total_size += sum(d.get('file_size', 0) for d in documents if d.get('file_size'))
            
            category = kb['category']
            categories[category] = categories.get(category, 0) + 1
        
        # БЗ с тестовыми вопросами
        kbs_with_tests = 0
        for kb in active_kbs:
            metadata = kb_manager.get_knowledge_base_metadata(kb['id'])
            if "relevance_test_questions" in metadata:
                kbs_with_tests += 1
        
        return {
            "total_knowledge_bases": total_kbs,
            "active_knowledge_bases": active_kbs_count,
            "total_documents": total_documents,
            "processed_documents": total_processed,
            "processing_rate": (total_processed / total_documents * 100) if total_documents > 0 else 0,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": categories,
            "knowledge_bases_with_tests": kbs_with_tests,
            "test_coverage": (kbs_with_tests / active_kbs_count * 100) if active_kbs_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения общей статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
