#!/usr/bin/env python3
"""
API Server for STECCOM Satellite Billing System
FastAPI-based REST API for database operations and RAG functionality
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
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

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class SQLQueryRequest(BaseModel):
    question: str
    company: Optional[str] = None
    username: Optional[str] = None

class RAGQueryRequest(BaseModel):
    question: str
    kb_id: Optional[int] = None
    role: Optional[str] = "user"

class QueryResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    sql_query: Optional[str] = None

# Authentication dependency
async def get_current_user(username: str = Query(...)):
    """Simple authentication check"""
    if not username:
        raise HTTPException(status_code=401, detail="Username required")
    return username

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

@app.post("/auth/login")
async def login(request: LoginRequest):
    """User authentication"""
    try:
        user_info = verify_login(request.username, request.password)
        if user_info:
            return {
                "success": True,
                "user": {
                    "username": user_info[0],
                    "company": user_info[1],
                    "role": user_info[2]
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {e}")
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
async def generate_sql_query(request: SQLQueryRequest):
    """Generate SQL query from natural language"""
    try:
        # Get company context if username provided
        company = request.company
        if request.username and not company:
            company = get_user_company(request.username)
        
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
    username: str = Depends(get_current_user)
):
    """Execute SQL query"""
    try:
        # Get user company for data filtering
        company = get_user_company(username)
        
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
async def rag_query(request: RAGQueryRequest):
    """Query RAG system"""
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        # Use RAG helper to get answer
        result = rag_helper.query(
            request.question,
            kb_id=request.kb_id,
            role=request.role
        )
        
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "question": request.question,
            "kb_id": request.kb_id,
            "role": request.role
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

@app.get("/users/{username}/company")
async def get_user_company_info(username: str):
    """Get user company information"""
    try:
        company = get_user_company(username)
        if company:
            return {
                "success": True,
                "username": username,
                "company": company
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"User company error: {e}")
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
    username: str = Depends(get_current_user)
):
    """Execute standard report"""
    try:
        if report_type not in STANDARD_QUERIES:
            raise HTTPException(status_code=404, detail=f"Report type '{report_type}' not found")
        
        # Get user company and role
        company = get_user_company(username)
        role = 'staff'  # TODO: Get actual role from user
        
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
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
async def get_session_state(username: str = Depends(get_current_user)):
    """Get user session state (placeholder)"""
    try:
        # TODO: Implement actual session state storage (Redis, database, etc.)
        return {
            "success": True,
            "username": username,
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
    username: str = Depends(get_current_user)
):
    """Save user session state (placeholder)"""
    try:
        # TODO: Implement actual session state storage (Redis, database, etc.)
        logger.info(f"Saving session state for {username}: {session_data}")
        
        return {
            "success": True,
            "username": username,
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
