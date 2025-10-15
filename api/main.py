"""
FastAPI Backend for СТЭККОМ Billing System
REST API для доступа к данным биллинга и интеграций
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import pandas as pd
from jose import jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta
import os
from pathlib import Path
import hashlib

# Import our existing modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from modules.core.database import execute_query, get_database_schema
from modules.core.queries import STANDARD_QUERIES
from modules.integrations import MediaWikiClient, KBToWikiPublisher
from modules.rag.multi_kb_rag import MultiKBRAG
from langchain_community.vectorstores import FAISS

# Import KB Admin API modules
sys.path.append(str(Path(__file__).parent.parent / "kb_admin"))
from kb_admin.modules.api.kb_test_questions_api import router as kb_test_questions_router
from kb_admin.modules.api.kb_management_api import router as kb_management_router

# FastAPI app
app = FastAPI(
    title="СТЭККОМ Unified API",
    description="REST API для системы спутниковой связи СТЭККОМ: биллинг, базы знаний и RAG",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include KB Admin API routers
app.include_router(kb_test_questions_router)
app.include_router(kb_management_router)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "steccom-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: Dict[str, Any]

class AgreementResponse(BaseModel):
    id: int
    tariff_name: str
    service_type: str
    unit: str
    price_per_unit: float
    monthly_fee: float
    traffic_limit: int
    start_date: str
    end_date: str
    status: str

class DeviceResponse(BaseModel):
    imei: str
    device_type: str
    model: str
    activated_at: str
    total_usage: Optional[int] = None
    total_amount: Optional[float] = None

class BillingRecordResponse(BaseModel):
    id: int
    billing_date: str
    usage_amount: int
    amount: float
    paid: bool
    payment_date: Optional[str] = None
    service_type: str
    unit: str

class ReportRequest(BaseModel):
    report_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    service_type: Optional[str] = None

class WikiPublishRequest(BaseModel):
    wiki_url: str
    username: str
    password: str
    namespace_prefix: str = "СТЭККОМ"
    kb_files: Optional[List[str]] = None

class RAGSearchRequest(BaseModel):
    query: str
    kb_names: Optional[List[str]] = None
    limit: int = 5

class RAGAskRequest(BaseModel):
    question: str
    kb_names: Optional[List[str]] = None

# Authentication functions
def verify_user_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials and return user info"""
    try:
        conn = sqlite3.connect('satellite_billing.db')
        c = conn.cursor()
        
        # Get user by username
        c.execute("SELECT id, username, company, role, password FROM users WHERE username = ?", 
                 (username,))
        user = c.fetchone()
        
        conn.close()
        
        if user:
            # Hash the provided password and compare with stored hash
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == user[4]:  # user[4] is the password field
                return {
                    "id": user[0],
                    "username": user[1],
                    "company": user[2],
                    "role": user[3],
                    "is_staff": user[3] == 'staff'
                }
        return None
    except Exception:
        return None

def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user.get("role") != required_role and not current_user.get("is_staff"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "СТЭККОМ Unified API",
        "version": "2.0.0",
        "description": "REST API для системы спутниковой связи СТЭККОМ",
        "features": [
            "Биллинг и тарифы",
            "Управление базами знаний",
            "RAG система для поиска",
            "Тестирование релевантности БЗ",
            "Интеграция с MediaWiki"
        ],
        "docs": "/docs",
        "endpoints": {
            "billing": "/agreements, /devices, /reports",
            "knowledge_bases": "/kb-management/knowledge-bases",
            "rag": "/rag/search, /rag/ask",
            "test_questions": "/kb-test-questions",
            "wiki": "/wiki/publish"
        }
    }

@app.post("/auth/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    user = verify_user_credentials(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token({
        "sub": user["username"],
        "company": user["company"],
        "role": user["role"],
        "is_staff": user["is_staff"]
    })
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_info=user
    )

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# Agreements endpoints
@app.get("/agreements/current", response_model=List[AgreementResponse])
async def get_current_agreements(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current active agreements for user's company"""
    try:
        query = STANDARD_QUERIES["Current agreement"]
        df, error = execute_query(query, (current_user["company"],))
        
        if error:
            raise HTTPException(status_code=500, detail=f"Database error: {error}")
        
        agreements = []
        for _, row in df.iterrows():
            agreements.append(AgreementResponse(
                id=0,  # Not in current query
                tariff_name=row.get("tariff_name", ""),
                service_type=row.get("service_type", ""),
                unit=row.get("unit", ""),
                price_per_unit=row.get("price_per_unit", 0.0),
                monthly_fee=row.get("monthly_fee", 0.0),
                traffic_limit=row.get("traffic_limit", 0),
                start_date=row.get("start_date", ""),
                end_date=row.get("end_date", ""),
                status=row.get("status", "")
            ))
        
        return agreements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agreements/history", response_model=List[AgreementResponse])
async def get_agreements_history(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all agreements history for user's company"""
    try:
        query = """
        SELECT 
            a.id,
            t.name as tariff_name,
            st.name as service_type,
            st.unit as unit,
            t.price_per_unit as price_per_unit,
            t.monthly_fee as monthly_fee,
            t.traffic_limit as traffic_limit,
            a.start_date as start_date,
            a.end_date as end_date,
            a.status as status
        FROM agreements a
        JOIN users u ON a.user_id = u.id
        JOIN tariffs t ON a.tariff_id = t.id
        JOIN service_types st ON t.service_type_id = st.id
        WHERE u.company = ?
        ORDER BY a.start_date DESC;
        """
        
        df, error = execute_query(query, (current_user["company"],))
        
        if error:
            raise HTTPException(status_code=500, detail=f"Database error: {error}")
        
        agreements = []
        for _, row in df.iterrows():
            agreements.append(AgreementResponse(
                id=row.get("id", 0),
                tariff_name=row.get("tariff_name", ""),
                service_type=row.get("service_type", ""),
                unit=row.get("unit", ""),
                price_per_unit=row.get("price_per_unit", 0.0),
                monthly_fee=row.get("monthly_fee", 0.0),
                traffic_limit=row.get("traffic_limit", 0),
                start_date=row.get("start_date", ""),
                end_date=row.get("end_date", ""),
                status=row.get("status", "")
            ))
        
        return agreements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Devices endpoints
@app.get("/devices", response_model=List[DeviceResponse])
async def get_devices(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get devices for user's company"""
    try:
        query = STANDARD_QUERIES["My devices"]
        df, error = execute_query(query, (current_user["company"],))
        
        if error:
            raise HTTPException(status_code=500, detail=f"Database error: {error}")
        
        devices = []
        for _, row in df.iterrows():
            devices.append(DeviceResponse(
                imei=row.get("device_id", ""),
                device_type=row.get("type", ""),
                model=row.get("model", ""),
                activated_at=row.get("activation_date", ""),
                total_usage=row.get("total_usage"),
                total_amount=row.get("total_amount")
            ))
        
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reports endpoints
@app.post("/reports/standard")
async def get_standard_report(
    report_request: ReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get standard report data"""
    try:
        # Map report types to queries
        query_map = {
            "current_agreement": STANDARD_QUERIES["Current agreement"],
            "my_devices": STANDARD_QUERIES["My devices"],
            "monthly_traffic": STANDARD_QUERIES["My monthly traffic"],
            "current_month_usage": STANDARD_QUERIES["Current month usage"]
        }
        
        if report_request.report_type not in query_map:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        query = query_map[report_request.report_type]
        df, error = execute_query(query, (current_user["company"],))
        
        if error:
            raise HTTPException(status_code=500, detail=f"Database error: {error}")
        
        return {
            "report_type": report_request.report_type,
            "data": df.to_dict("records"),
            "total_records": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/available")
async def get_available_reports():
    """Get list of available standard reports"""
    return {
        "reports": [
            {"id": "current_agreement", "name": "Текущий договор"},
            {"id": "my_devices", "name": "Список устройств"},
            {"id": "monthly_traffic", "name": "Трафик за месяц"},
            {"id": "current_month_usage", "name": "Использование за текущий месяц"}
        ]
    }

# Wiki integration endpoints
@app.post("/wiki/publish")
async def publish_to_wiki(
    wiki_request: WikiPublishRequest,
    current_user: Dict[str, Any] = Depends(require_role("staff"))
):
    """Publish KB to MediaWiki"""
    try:
        client = MediaWikiClient(
            wiki_url=wiki_request.wiki_url,
            username=wiki_request.username,
            password=wiki_request.password
        )
        
        publisher = KBToWikiPublisher(client)
        
        if wiki_request.kb_files:
            # Publish specific files
            results = {}
            for kb_file in wiki_request.kb_files:
                file_results = publisher.publish_kb_file(kb_file, wiki_request.namespace_prefix)
                results[kb_file] = file_results
        else:
            # Publish all files
            results = publisher.publish_all_kb_files("docs/kb", wiki_request.namespace_prefix)
        
        return {
            "success": True,
            "message": "Publishing completed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wiki/test-connection")
async def test_wiki_connection(
    wiki_url: str,
    username: str,
    password: str,
    current_user: Dict[str, Any] = Depends(require_role("staff"))
):
    """Test MediaWiki connection"""
    try:
        client = MediaWikiClient(wiki_url, username, password)
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RAG System endpoints
@app.get("/rag/status")
async def get_rag_status():
    """Get RAG system status and loaded knowledge bases"""
    try:
        rag_system = MultiKBRAG()
        status = rag_system.get_status()
        return status
    except Exception as e:
        return {"status": "error", "message": str(e), "loaded_kbs": []}

@app.post("/rag/search")
async def search_knowledge_base(
    search_request: RAGSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search in knowledge bases using RAG"""
    try:
        rag_system = MultiKBRAG()
        results = rag_system.search(
            search_request.query, 
            kb_names=search_request.kb_names, 
            limit=search_request.limit
        )
        return {
            "query": search_request.query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/ask")
async def ask_question(
    ask_request: RAGAskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Ask a question using RAG system"""
    try:
        rag_system = MultiKBRAG()
        answer = rag_system.ask_question(ask_request.question, kb_names=ask_request.kb_names)
        return {
            "question": ask_request.question,
            "answer": answer["answer"],
            "sources": answer.get("sources", []),
            "kb_used": answer.get("kb_used", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/knowledge-bases")
async def get_knowledge_bases(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get list of available knowledge bases"""
    try:
        rag_system = MultiKBRAG()
        kbs = rag_system.get_available_kbs()
        return {"knowledge_bases": kbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/load-all")
async def load_all_knowledge_bases(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Load all active knowledge bases"""
    try:
        rag_system = MultiKBRAG()
        loaded_count = rag_system.load_all_active_kbs()
        return {
            "message": f"Loaded {loaded_count} knowledge bases",
            "loaded_count": loaded_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/load-kb-files")
async def load_kb_files_directly(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Load KB files directly from docs/kb/ folder"""
    try:
        import json
        from pathlib import Path
        
        kb_dir = Path("docs/kb")
        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail="KB directory not found")
        
        rag_system = MultiKBRAG()
        loaded_count = 0
        
        # Загружаем каждый KB файл
        for kb_file in kb_dir.glob("*.json"):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                # Создаем документы из KB данных
                documents = []
                for item in kb_data:
                    if isinstance(item, dict):
                        content = json.dumps(item, ensure_ascii=False)
                        doc_metadata = {
                            'source': str(kb_file),
                            'title': item.get('title', 'Unknown'),
                            'category': item.get('category', 'Unknown')
                        }
                        documents.append({
                            'content': content,
                            'metadata': doc_metadata
                        })
                
                # Добавляем документы в RAG систему
                if documents:
                    # Создаем временную KB для этого файла
                    kb_name = f"KB_{kb_file.stem}"
                    rag_system.kb_metadata[len(rag_system.kb_metadata) + 1] = {
                        'name': kb_name,
                        'category': 'KB Files',
                        'description': f'Knowledge base from {kb_file.name}'
                    }
                    
                    # Создаем векторное хранилище для документов
                    from langchain.schema import Document
                    langchain_docs = [Document(page_content=doc['content'], metadata=doc['metadata']) for doc in documents]
                    
                    if langchain_docs:
                        vectorstore = FAISS.from_documents(langchain_docs, rag_system.embeddings)
                        rag_system.vectorstores[len(rag_system.vectorstores) + 1] = vectorstore
                        loaded_count += 1
                        
            except Exception as e:
                print(f"Error loading {kb_file}: {e}")
                continue
        
        return {
            "message": f"Loaded {loaded_count} KB files directly",
            "loaded_count": loaded_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search-kb-files")
async def search_kb_files_directly(
    search_request: RAGSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search directly in KB files without loading into RAG system"""
    try:
        import json
        from pathlib import Path
        
        kb_dir = Path("docs/kb")
        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail="KB directory not found")
        
        results = []
        query_lower = search_request.query.lower()
        
        # Ищем во всех KB файлах
        for kb_file in kb_dir.glob("*.json"):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                # Ищем совпадения в KB данных
                for item in kb_data:
                    if isinstance(item, dict):
                        # Проверяем заголовок
                        title = item.get('title', '')
                        if query_lower in title.lower():
                            results.append({
                                "content": json.dumps(item, ensure_ascii=False, indent=2),
                                "metadata": {
                                    "source": str(kb_file),
                                    "title": title,
                                    "category": item.get('category', 'Unknown'),
                                    "match_type": "title"
                                },
                                "kb_name": f"KB_{kb_file.stem}",
                                "kb_category": "KB Files"
                            })
                            continue
                        
                        # Проверяем содержимое
                        content_text = json.dumps(item, ensure_ascii=False).lower()
                        if query_lower in content_text:
                            results.append({
                                "content": json.dumps(item, ensure_ascii=False, indent=2),
                                "metadata": {
                                    "source": str(kb_file),
                                    "title": title,
                                    "category": item.get('category', 'Unknown'),
                                    "match_type": "content"
                                },
                                "kb_name": f"KB_{kb_file.stem}",
                                "kb_category": "KB Files"
                            })
                            
            except Exception as e:
                print(f"Error searching in {kb_file}: {e}")
                continue
        
        # Ограничиваем результаты
        results = results[:search_request.limit]
        
        return {
            "query": search_request.query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = sqlite3.connect('satellite_billing.db')
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
