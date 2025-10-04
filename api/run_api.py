#!/usr/bin/env python3
"""
API Server for STECCOM Satellite Billing System
FastAPI-based REST API for database operations and RAG functionality
"""

import os
import sys
import logging
import secrets
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
import pandas as pd

# Import our modules
from modules.core.database import (
    init_db, get_database_schema, execute_query, execute_standard_query,
    get_user_company, verify_login
)
from modules.core.rag import generate_sql
from modules.core.queries import STANDARD_QUERIES, QUICK_QUESTIONS
from modules.rag.rag_helper import RAGHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="STECCOM API",
    description="API для системы спутниковой связи СТЭККОМ",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Initialize RAG helper
try:
    rag_helper = RAGHelper()
    RAG_AVAILABLE = True
    logger.info("RAG Helper initialized successfully")
except Exception as e:
    RAG_AVAILABLE = False
    logger.warning(f"RAG Helper not available: {e}")

# Token management
security = HTTPBearer()
active_tokens = {}  # In production, use Redis or database

def generate_token(username: str, role: str, company: str) -> str:
    """Generate a secure token for user"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)  # 24 hour expiry
    
    active_tokens[token] = {
        "username": username,
        "role": role,
        "company": company,
        "expires_at": expires_at,
        "created_at": datetime.now()
    }
    
    logger.info(f"Generated token for user: {username}")
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """Verify token and return user info"""
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token_info = active_tokens[token]
    
    # Check if token expired
    if datetime.now() > token_info["expires_at"]:
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return token_info

def revoke_token(token: str) -> bool:
    """Revoke a token"""
    if token in active_tokens:
        del active_tokens[token]
        logger.info(f"Token revoked: {token[:8]}...")
        return True
    return False

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[Dict[str, str]] = None
    expires_at: Optional[str] = None

class SQLQueryRequest(BaseModel):
    question: str
    company: Optional[str] = None

class RAGQueryRequest(BaseModel):
    question: str
    kb_id: Optional[int] = None
    role: Optional[str] = "user"

class QueryResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    sql_query: Optional[str] = None

class TokenInfo(BaseModel):
    username: str
    role: str
    company: str
    expires_at: str
    created_at: str

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Token-based authentication"""
    try:
        token = credentials.credentials
        user_info = verify_token(token)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "STECCOM API Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "rag_available": RAG_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """User authentication with token generation"""
    try:
        user_info = verify_login(request.username, request.password)
        if user_info:
            success, role, company = user_info
            if success:
                # Generate token
                token = generate_token(request.username, role, company)
                token_info = active_tokens[token]
                
                return LoginResponse(
                    success=True,
                    token=token,
                    user={
                        "username": request.username,
                        "company": company,
                        "role": role
                    },
                    expires_at=token_info["expires_at"].isoformat()
                )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout and revoke token"""
    try:
        # Find and revoke the current token
        for token, info in active_tokens.items():
            if info["username"] == current_user["username"]:
                revoke_token(token)
                break
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/token-info", response_model=TokenInfo)
async def get_token_info(current_user: dict = Depends(get_current_user)):
    """Get current token information"""
    try:
        return TokenInfo(
            username=current_user["username"],
            role=current_user["role"],
            company=current_user["company"],
            expires_at=current_user["expires_at"].isoformat(),
            created_at=current_user["created_at"].isoformat()
        )
    except Exception as e:
        logger.error(f"Token info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/schema")
async def get_schema():
    """Get database schema"""
    try:
        schema = get_database_schema()
        return {
            "success": True,
            "schema": schema
        }
    except Exception as e:
        logger.error(f"Schema error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sql/generate")
async def generate_sql_query(
    request: SQLQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate SQL query from natural language"""
    try:
        # Use company from token or request
        company = request.company or current_user["company"]
        
        # Generate SQL
        sql_query = generate_sql(request.question, company)
        
        return {
            "success": True,
            "sql_query": sql_query,
            "question": request.question,
            "company": company
        }
    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sql/execute")
async def execute_sql_query(
    sql_query: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Execute SQL query"""
    try:
        # Get user company for data filtering
        company = current_user["company"]
        
        # Execute query
        df, error = execute_query(sql_query)
        
        if error:
            return {
                "success": False,
                "error": error,
                "sql_query": sql_query
            }
        
        # Convert DataFrame to JSON
        data = df.to_dict('records') if not df.empty else []
        
        return {
            "success": True,
            "data": data,
            "sql_query": sql_query,
            "company": company,
            "row_count": len(data)
        }
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
async def rag_query(
    request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Query RAG system"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        # Use role from token or request
        role = request.role or current_user["role"]
        
        # Use RAG helper to get answer
        result = rag_helper.query(
            request.question,
            kb_id=request.kb_id,
            role=role
        )
        
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "question": request.question,
            "kb_id": request.kb_id,
            "role": role
        }
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/knowledge-bases")
async def list_knowledge_bases():
    """List available knowledge bases"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        # Get list of knowledge bases
        kbs = rag_helper.list_knowledge_bases()
        
        return {
            "success": True,
            "knowledge_bases": kbs
        }
    except Exception as e:
        logger.error(f"KB list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    try:
        return {
            "success": True,
            "username": current_user["username"],
            "company": current_user["company"],
            "role": current_user["role"]
        }
    except Exception as e:
        logger.error(f"User info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.get("/reports/standard")
async def get_standard_reports():
    """Get list of available standard reports"""
    try:
        return {
            "success": True,
            "reports": list(STANDARD_QUERIES.keys()),
            "quick_questions": QUICK_QUESTIONS
        }
    except Exception as e:
        logger.error(f"Standard reports error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/standard/{report_type}")
async def execute_standard_report(
    report_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Execute standard report"""
    try:
        if report_type not in STANDARD_QUERIES:
            raise HTTPException(status_code=404, detail=f"Report type '{report_type}' not found")
        
        # Get user company and role from token
        company = current_user["company"]
        role = current_user["role"]
        
        # Execute standard query
        df, error = execute_standard_query(report_type, company, role)
        
        if error:
            return {
                "success": False,
                "error": error,
                "report_type": report_type
            }
        
        # Convert DataFrame to JSON
        data = df.to_dict('records') if not df.empty else []
        
        return {
            "success": True,
            "data": data,
            "report_type": report_type,
            "company": company,
            "row_count": len(data)
        }
    except Exception as e:
        logger.error(f"Standard report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/csv")
async def export_csv(
    sql_query: str = Query(...),
    filename: str = Query(default="export.csv"),
    current_user: dict = Depends(get_current_user)
):
    """Export data as CSV"""
    try:
        # Execute query
        df, error = execute_query(sql_query)
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        # Convert to CSV
        csv_data = df.to_csv(index=False)
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/charts/create")
async def create_chart_endpoint(
    data: List[Dict],
    chart_type: str = "line",
    title: str = "Chart",
    current_user: dict = Depends(get_current_user)
):
    """Create chart from data"""
    try:
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Basic chart info (simplified version)
        chart_info = {
            "chart_type": chart_type,
            "title": title,
            "data_points": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(5).to_dict('records') if not df.empty else []
        }
        
        return {
            "success": True,
            "chart_info": chart_info,
            "message": f"Chart created with {len(df)} data points"
        }
    except Exception as e:
        logger.error(f"Chart creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/state")
async def get_session_state(current_user: dict = Depends(get_current_user)):
    """Get user session state (placeholder)"""
    try:
        # TODO: Implement actual session state storage (Redis, database, etc.)
        return {
            "success": True,
            "username": current_user["username"],
            "session_data": {
                "last_query": None,
                "favorite_reports": [],
                "preferences": {}
            },
            "message": "Session state placeholder - implement actual storage"
        }
    except Exception as e:
        logger.error(f"Session state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/state")
async def save_session_state(
    session_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Save user session state (placeholder)"""
    try:
        # TODO: Implement actual session state storage (Redis, database, etc.)
        logger.info(f"Saving session state for {current_user['username']}: {session_data}")
        
        return {
            "success": True,
            "username": current_user["username"],
            "message": "Session state saved (placeholder - implement actual storage)"
        }
    except Exception as e:
        logger.error(f"Session state save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "run_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
