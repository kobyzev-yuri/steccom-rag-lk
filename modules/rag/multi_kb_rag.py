"""
Multi Knowledge Base RAG System
Система RAG для работы с несколькими базами знаний
"""

import streamlit as st
import json
import sqlite3
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    print("⚠️ HuggingFaceEmbeddings недоступен: langchain_huggingface не установлен")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
import os
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.schema import Document

class MultiKBRAG:
    def __init__(self, db_path: str = "satellite_billing.db",
                 chat_provider: Optional[str] = None,
                 chat_model: Optional[str] = None,
                 proxy_base_url: Optional[str] = None,
                 proxy_api_key: Optional[str] = None,
                 temperature: float = 0.2):
        self.db_path = db_path
        # Embeddings backend: default to multilingual HF model if configured
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
        if embedding_provider in ("hf", "huggingface") and HUGGINGFACE_AVAILABLE:
            embedding_model = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model, 
                                                    model_kwargs={"device": "cpu"},
                                                    encode_kwargs={"normalize_embeddings": True})
            self._embedding_backend = {"provider": "huggingface", "model": embedding_model}
        else:
            # Используем Ollama по умолчанию
            self.embeddings = OllamaEmbeddings(model=os.getenv("OLLAMA_EMBED_MODEL", "all-minilm"))
            self._embedding_backend = {"provider": "ollama", "model": os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")}
        # Resolve chat backend configuration (constructor overrides env)
        env_use_proxy = os.getenv("USE_PROXYAPI", "false").lower() == "true"
        resolved_provider = (chat_provider or ("proxyapi" if env_use_proxy else "ollama")).lower()
        resolved_temperature = float(os.getenv("PROXYAPI_TEMPERATURE", str(temperature)))
        if resolved_provider == "proxyapi":
            resolved_base_url = proxy_base_url or os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
            # Support OPEN_AI_API_KEY as proxyapi key alias
            resolved_api_key = proxy_api_key or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY", "")
            resolved_model = chat_model or os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o")
            self.chat_model = ChatOpenAI(
                model=resolved_model,
                openai_api_key=resolved_api_key,
                base_url=resolved_base_url,
                temperature=resolved_temperature
            )
            self._chat_backend = {
                'provider': 'proxyapi', 'model': resolved_model,
                'base_url': resolved_base_url, 'temperature': resolved_temperature
            }
        elif resolved_provider == "openai":
            # Direct OpenAI usage (no custom base_url)
            resolved_model = chat_model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            self.chat_model = ChatOpenAI(
                model=resolved_model,
                openai_api_key=openai_key,
                temperature=resolved_temperature
            )
            self._chat_backend = {'provider': 'openai', 'model': resolved_model, 'temperature': resolved_temperature}
        else:
            resolved_model = chat_model or os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b")
            self.chat_model = ChatOllama(model=resolved_model)
            self._chat_backend = {'provider': 'ollama', 'model': resolved_model}
        self.vectorstores = {}  # kb_id -> vectorstore
        self.kb_metadata = {}   # kb_id -> metadata
        self.kb_chunks = {}     # kb_id -> List[Document]

    def set_chat_backend(self, provider: str, model: str,
                         base_url: Optional[str] = None,
                         api_key: Optional[str] = None,
                         temperature: float = 0.2) -> None:
        """Reconfigure chat backend without touching vector stores."""
        provider = (provider or "ollama").lower()
        if provider == "proxyapi":
            self.chat_model = ChatOpenAI(
                model=model,
                openai_api_key=api_key or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY", ""),
                base_url=base_url or os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
                temperature=temperature
            )
            self._chat_backend = {
                'provider': 'proxyapi', 'model': model,
                'base_url': base_url, 'temperature': temperature
            }
        elif provider == "openai":
            self.chat_model = ChatOpenAI(
                model=model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
                openai_api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
                temperature=temperature
            )
            self._chat_backend = {'provider': 'openai', 'model': model, 'temperature': temperature}
        else:
            self.chat_model = ChatOllama(model=model or os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b"))
            self._chat_backend = {'provider': 'ollama', 'model': model}

    def _ensure_usage_table(self) -> None:
        """Create llm_usage table if not exists."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                question TEXT,
                response_length INTEGER
            )
            """
        )
        conn.commit()
        conn.close()

    def _log_llm_usage(self, provider: Optional[str], model: Optional[str],
                        prompt_tokens: Optional[int], completion_tokens: Optional[int],
                        total_tokens: Optional[int], question: str,
                        response_length: int) -> None:
        """Insert usage row into llm_usage table."""
        self._ensure_usage_table()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO llm_usage (
                timestamp, provider, model, prompt_tokens, completion_tokens, total_tokens, question, response_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                provider, model,
                prompt_tokens if isinstance(prompt_tokens, int) else None,
                completion_tokens if isinstance(completion_tokens, int) else None,
                total_tokens if isinstance(total_tokens, int) else None,
                question, int(response_length)
            )
        )
        conn.commit()
        conn.close()
        self.vectorstores = {}  # kb_id -> vectorstore
        self.kb_metadata = {}   # kb_id -> metadata
        
    def load_knowledge_base(self, kb_id: int) -> bool:
        """Load specific knowledge base into memory"""
        try:
            # Get KB info from database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT * FROM knowledge_bases WHERE id = ? AND is_active = 1", (kb_id,))
            kb_info = c.fetchone()
            
            if not kb_info:
                conn.close()
                return False
            
            # Get documents for this KB
            c.execute('''
                SELECT * FROM knowledge_documents 
                WHERE kb_id = ? AND processed = 1
                ORDER BY upload_date DESC
            ''', (kb_id,))
            
            documents = c.fetchall()
            conn.close()
            
            if not documents:
                return False
            
            # Process documents into vectorstore
            documents_list = []
            for doc in documents:
                # Load document content
                doc_path = doc[3]  # file_path column
                if doc_path and Path(doc_path).exists():
                    content = ""
                    extraction_error = None
                    # First attempt: PyPDF2
                    try:
                        import PyPDF2
                        with open(doc_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            for page in pdf_reader.pages:
                                extracted = page.extract_text() or ""
                                content += extracted + "\n"
                    except Exception as e:
                        extraction_error = str(e)

                    # Fallback: PyMuPDF (fitz) if content is still too small
                    if len(content.strip()) < 50:
                        try:
                            import fitz  # PyMuPDF
                            with fitz.open(doc_path) as pdf_doc:
                                content = "\n".join([page.get_text() or "" for page in pdf_doc])
                        except Exception as e:
                            # keep previous error if any
                            extraction_error = extraction_error or str(e)

                    # If still empty, create minimal placeholder
                    if not content.strip():
                        content = f"Документ: {doc[2]} (файл: {Path(doc_path).name}) — текст не извлечен."

                    # Append document regardless so KB can load
                    doc_metadata = {
                        'kb_id': kb_id,
                        'doc_id': doc[0],
                        'title': doc[2],
                        'source': doc_path,
                        'category': kb_info[3]
                    }
                    if extraction_error:
                        doc_metadata['extraction_error'] = extraction_error

                    documents_list.append(Document(
                        page_content=content,
                        metadata=doc_metadata
                    ))
            
            if not documents_list:
                # Should not happen, but guard: create one placeholder to allow KB to load
                documents_list.append(Document(
                    page_content=f"База знаний {kb_info[1]} не содержит доступных документов.",
                    metadata={
                        'kb_id': kb_id,
                        'doc_id': -1,
                        'title': 'Пустая база знаний',
                        'source': 'db',
                        'category': kb_info[3]
                    }
                ))
            
            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            # Split documents
            chunks = text_splitter.split_documents(documents_list)
            
            # Create vectorstore
            vectorstore = FAISS.from_documents(chunks, self.embeddings)
            
            # Store in memory
            self.vectorstores[kb_id] = vectorstore
            self.kb_metadata[kb_id] = {
                'name': kb_info[1],
                'description': kb_info[2],
                'category': kb_info[3],
                'doc_count': len(documents_list),
                'chunk_count': len(chunks)
            }
            self.kb_chunks[kb_id] = chunks
            
            return True
            
        except Exception as e:
            st.error(f"Ошибка загрузки базы знаний {kb_id}: {e}")
            return False
    
    def load_all_active_kbs(self) -> int:
        """Load all active knowledge bases"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT id FROM knowledge_bases WHERE is_active = 1")
        kb_ids = [row[0] for row in c.fetchall()]
        conn.close()
        
        loaded_count = 0
        for kb_id in kb_ids:
            if self.load_knowledge_base(kb_id):
                loaded_count += 1
        
        return loaded_count
    
    def get_available_kbs(self) -> List[Dict]:
        """Get list of available knowledge bases"""
        return [
            {
                'kb_id': kb_id,
                **metadata
            }
            for kb_id, metadata in self.kb_metadata.items()
        ]
    
    def search_across_kbs(self, query: str, kb_ids: List[int] = None, k: int = 5) -> List[Document]:
        """Search across multiple knowledge bases with hybrid search"""
        if kb_ids is None:
            kb_ids = list(self.vectorstores.keys())
        
        all_results = []
        
        for kb_id in kb_ids:
            if kb_id in self.vectorstores:
                # Vector search
                vectorstore = self.vectorstores[kb_id]
                vector_results = vectorstore.similarity_search(query, k=k)
                
                # Add KB metadata to results
                for doc in vector_results:
                    doc.metadata['kb_name'] = self.kb_metadata[kb_id]['name']
                    doc.metadata['kb_category'] = self.kb_metadata[kb_id]['category']
                
                all_results.extend(vector_results)
                
                # Text search for exact matches
                text_results = self._text_search_in_kb(query, kb_id, k)
                all_results.extend(text_results)
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_documents(all_results)
        return unique_results[:k*len(kb_ids)]
    
    def search_in_kb(self, query: str, kb_id: int, k: int = 5) -> List[Document]:
        """Search within specific knowledge base"""
        if kb_id not in self.vectorstores:
            return []
        
        vectorstore = self.vectorstores[kb_id]
        results = vectorstore.similarity_search(query, k=k)
        
        # Add KB metadata
        for doc in results:
            doc.metadata['kb_name'] = self.kb_metadata[kb_id]['name']
            doc.metadata['kb_category'] = self.kb_metadata[kb_id]['category']
        
        return results
    
    def _text_search_in_kb(self, query: str, kb_id: int, k: int = 5) -> List[Document]:
        """Strong keyword search over stored chunks within specific knowledge base"""
        if kb_id not in self.kb_chunks:
            return []
        
        query_lower = query.lower()
        terms = [t for t in query_lower.replace('\n', ' ').split() if len(t) > 2]
        # Add domain-specific boosts
        boosts = {
            'детализирован': 5,
            'отчет': 3,
            'формат': 3,
            'трафик': 2,
        }
        
        scored = []
        for doc in self.kb_chunks[kb_id]:
            text = doc.page_content.lower()
            score = 0
            for t in terms:
                cnt = text.count(t)
                if cnt:
                    score += cnt * boosts.get(t, 1)
            # phrase boost
            if 'детализированного отчета' in text:
                score += 20
            if score > 0:
                new_meta = dict(doc.metadata)
                new_meta['kb_name'] = self.kb_metadata[kb_id]['name']
                new_meta['kb_category'] = self.kb_metadata[kb_id]['category']
                new_meta['search_type'] = 'keyword_match'
                scored.append((score, Document(page_content=doc.page_content, metadata=new_meta)))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:k]]
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """Remove duplicate documents based on content"""
        seen_content = set()
        unique_docs = []
        
        for doc in documents:
            content_hash = hash(doc.page_content[:100])  # Use first 100 chars as identifier
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def get_response_with_context(self, question: str, kb_ids: List[int] = None, 
                                 context_limit: int = 3) -> str:
        """Get response using RAG with specific knowledge bases"""
        try:
            # Search for relevant documents
            relevant_docs = self.search_across_kbs(question, kb_ids, k=context_limit)
            
            if not relevant_docs:
                return "Не найдено релевантной информации в базах знаний."
            
            # Format context
            context = self._format_documents(relevant_docs)
            
            # Create prompt
            template = """Ты - эксперт по спутниковой связи и телекоммуникациям. 
            Отвечай на вопросы пользователя, используя предоставленный контекст.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ПРАВИЛА ОТВЕТА:
1. Отвечай ТОЛЬКО на русском языке
2. Используй информацию из контекста - ищи точные совпадения и релевантные фрагменты
3. Если информации недостаточно, честно скажи об этом
4. Будь точным и профессиональным
5. Указывай источники информации (название документа)
6. Если в контексте есть точная информация по вопросу, обязательно используй её
7. Не придумывай информацию, которой нет в контексте

ОТВЕТ:"""

            prompt = ChatPromptTemplate.from_template(template)
            # Keep model output as AIMessage to access usage metadata when available
            chain = prompt | self.chat_model
            
            model_output = chain.invoke({
                "context": context,
                "question": question
            })
            
            # Extract text content
            response_text = getattr(model_output, 'content', None) or str(model_output)
            
            # Try to capture usage metadata (supported by ChatOpenAI backends)
            usage = getattr(model_output, 'usage_metadata', None)
            if usage is None:
                # Some integrations place usage under response_metadata
                metadata = getattr(model_output, 'response_metadata', {}) or {}
                usage = metadata.get('token_usage') or metadata.get('usage')
            
            # Log usage if any
            try:
                self._log_llm_usage(
                    provider=self._chat_backend.get('provider'),
                    model=self._chat_backend.get('model'),
                    prompt_tokens=(usage or {}).get('prompt_tokens'),
                    completion_tokens=(usage or {}).get('completion_tokens'),
                    total_tokens=(usage or {}).get('total_tokens'),
                    question=question,
                    response_length=len(response_text or ""),
                )
            except Exception:
                pass
            
            return response_text
            
        except Exception as e:
            return f"Ошибка получения ответа: {e}"
    
    def _format_documents(self, docs: List[Document]) -> str:
        """Format documents for context"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            kb_name = doc.metadata.get('kb_name', 'Неизвестная БЗ')
            title = doc.metadata.get('title', 'Без названия')
            search_type = doc.metadata.get('search_type', 'vector_search')
            
            # Show more content for better context
            content = doc.page_content[:800] if len(doc.page_content) > 800 else doc.page_content
            
            formatted.append(f"""
Документ {i} (из БЗ: {kb_name}):
Название: {title}
Тип поиска: {search_type}
Содержание: {content}
""")
        
        return "\n".join(formatted)
    
    def get_kb_statistics(self) -> Dict:
        """Get statistics about loaded knowledge bases"""
        total_docs = sum(metadata['doc_count'] for metadata in self.kb_metadata.values())
        total_chunks = sum(metadata['chunk_count'] for metadata in self.kb_metadata.values())
        
        return {
            'loaded_kbs': len(self.vectorstores),
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'kb_details': self.kb_metadata
        }
    
    def reload_kb(self, kb_id: int) -> bool:
        """Reload specific knowledge base"""
        if kb_id in self.vectorstores:
            del self.vectorstores[kb_id]
        if kb_id in self.kb_metadata:
            del self.kb_metadata[kb_id]
        
        return self.load_knowledge_base(kb_id)
    
    def clear_all(self):
        """Clear all loaded knowledge bases"""
        self.vectorstores.clear()
        self.kb_metadata.clear()
