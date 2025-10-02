"""
KB Admin RAG System
RAG система для работы с базами знаний из KB Admin
"""

import streamlit as st
import json
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


class KBAdminRAG:
    """RAG система для работы с базами знаний из KB Admin"""
    
    def __init__(self, kb_admin_path: str = None,
                 chat_provider: Optional[str] = None,
                 chat_model: Optional[str] = None,
                 proxy_base_url: Optional[str] = None,
                 proxy_api_key: Optional[str] = None,
                 temperature: float = 0.2):
        
        if kb_admin_path is None:
            current_dir = Path(__file__).parent
            self.kb_admin_path = current_dir.parent.parent / "kb_admin"
        else:
            self.kb_admin_path = Path(kb_admin_path)
        
        self.json_kb_path = self.kb_admin_path / "docs" / "kb"
        
        # Embeddings configuration
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
        if embedding_provider in ("hf", "huggingface") and HUGGINGFACE_AVAILABLE:
            embedding_model = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
            print(f"✅ Используем HuggingFace embeddings: {embedding_model}")
        else:
            ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            self.embeddings = OllamaEmbeddings(model=ollama_model)
            print(f"✅ Используем Ollama embeddings: {ollama_model}")
        
        # Chat model configuration
        resolved_provider = (chat_provider or os.getenv("CHAT_PROVIDER", "ollama")).lower()
        resolved_temperature = temperature or float(os.getenv("CHAT_TEMPERATURE", "0.2"))
        
        if resolved_provider == "proxyapi":
            resolved_model = chat_model or os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o")
            proxy_key = proxy_api_key or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPEN_AI_API_KEY", "")
            proxy_url = proxy_base_url or os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
            self.chat_model = ChatOpenAI(
                model=resolved_model,
                openai_api_key=proxy_key,
                base_url=proxy_url,
                temperature=resolved_temperature
            )
            self._chat_backend = {
                'provider': 'proxyapi', 'model': resolved_model,
                'base_url': proxy_base_url, 'temperature': resolved_temperature
            }
        elif resolved_provider == "openai":
            resolved_model = chat_model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            self.chat_model = ChatOpenAI(
                model=resolved_model,
                openai_api_key=openai_key,
                temperature=resolved_temperature
            )
            self._chat_backend = {'provider': 'openai', 'model': resolved_model, 'temperature': resolved_temperature}
        else:
            resolved_model = chat_model or os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:latest")
            self.chat_model = ChatOllama(model=resolved_model, timeout=60)
            self._chat_backend = {'provider': 'ollama', 'model': resolved_model}
        
        self.vectorstores = {}
        self.kb_metadata = {}
        self.kb_chunks = {}
        
        try:
            self.load_all_kb_admin_kbs()
        except Exception as e:
            print(f"⚠️ Не удалось загрузить базы знаний из KB Admin: {e}")
    
    def load_all_active_kbs(self) -> int:
        """Load all active knowledge bases - compatibility method"""
        return self.load_all_kb_admin_kbs()
    
    def load_all_kb_admin_kbs(self) -> int:
        """Load all KB Admin knowledge bases from JSON files"""
        if not self.json_kb_path.exists():
            print(f"⚠️ Директория KB Admin не найдена: {self.json_kb_path}")
            return 0
        
        loaded_count = 0
        for json_file in self.json_kb_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                kb_info = kb_data.get('kb_info', {})
                kb_id = kb_info.get('id')
                
                if kb_id is None:
                    print(f"❌ JSON файл {json_file.name} не содержит 'id' в 'kb_info'")
                    continue
                
                if self.load_knowledge_base_from_json(kb_id, kb_data):
                    loaded_count += 1
            except Exception as e:
                print(f"❌ Ошибка загрузки KB {json_file.name}: {e}")
        
        print(f"✅ Загружено активных БЗ из KB Admin: {loaded_count}")
        return loaded_count
    
    def load_knowledge_base_from_json(self, kb_id: int, kb_data: Dict) -> bool:
        """Load specific knowledge base from JSON data into memory"""
        try:
            kb_info = kb_data.get('kb_info', {})
            documents = kb_data.get('documents', [])
            
            if not documents:
                print(f"⚠️ KB {kb_id} не содержит документов")
                return False
            
            documents_list = []
            for doc in documents:
                metadata_str = doc.get('metadata', '{}')
                if isinstance(metadata_str, str):
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        metadata = {}
                else:
                    metadata = metadata_str
                
                content = metadata.get('content', '')
                
                if content:
                    documents_list.append(Document(
                        page_content=content,
                        metadata={
                            'kb_id': kb_id,
                            'doc_id': doc.get('id'),
                            'title': doc.get('title', ''),
                            'source': 'kb_admin_json',
                            'category': kb_info.get('category', ''),
                            'kb_name': kb_info.get('name', ''),
                            'kb_category': kb_info.get('category', '')
                        }
                    ))
            
            if not documents_list:
                print(f"⚠️ KB {kb_id} не содержит доступного контента")
                return False
            
            # Split documents into chunks
            chunks = []
            for d in documents_list:
                splitter = self._pick_splitter_for(d.page_content)
                chunks.extend(splitter.split_documents([d]))
            
            # Create vectorstore
            vectorstore = FAISS.from_documents(chunks, self.embeddings)
            
            self.vectorstores[kb_id] = vectorstore
            self.kb_metadata[kb_id] = {
                'name': kb_info.get('name', f"KB {kb_id}"),
                'description': kb_info.get('description', ''),
                'category': kb_info.get('category', ''),
                'doc_count': len(documents_list),
                'chunk_count': len(chunks)
            }
            
            print(f"✅ Загружена KB {kb_id}: {self.kb_metadata[kb_id]['name']} - {len(documents_list)} документов, {len(chunks)} чанков")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки KB {kb_id}: {e}")
            return False
    
    def _pick_splitter_for(self, text: str) -> RecursiveCharacterTextSplitter:
        """Choose appropriate text splitter based on content"""
        if len(text) < 1000:
            return RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ".", "!", "?", ";", " ", ""]
            )
        else:
            return RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separators=["\n\n", "\n", ".", "!", "?", ";", " ", ""]
            )
    
    def search_across_kbs(self, query: str, kb_ids: List[int] = None, k: int = 3) -> List[Document]:
        """Search across specified knowledge bases"""
        if kb_ids is None:
            kb_ids = list(self.vectorstores.keys())
        
        all_results = []
        for kb_id in kb_ids:
            if kb_id in self.vectorstores:
                try:
                    results = self.vectorstores[kb_id].similarity_search(query, k=k)
                    all_results.extend(results)
                except Exception as e:
                    print(f"❌ Ошибка поиска в KB {kb_id}: {e}")
        
        # Sort by relevance (simple approach)
        return all_results[:k]
    
    def _format_documents(self, docs: List[Document]) -> str:
        """Format documents for prompt"""
        if not docs:
            return "Контекст не найден."
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            kb_name = doc.metadata.get('kb_name', 'Неизвестная БЗ')
            title = doc.metadata.get('title', 'Без названия')
            content = doc.page_content
            
            formatted.append(f"Документ {i} (из БЗ: {kb_name}):")
            formatted.append(f"Название: {title}")
            formatted.append(f"Содержание: {content}")
            formatted.append("")
        
        return "\n".join(formatted)
    
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
            template = """
Ты — ассистент биллинга. Отвечай строго ПО КОНТЕКСТУ из базы знаний.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ПРАВИЛА ОТВЕТА (ОБЯЗАТЕЛЬНЫ):
1) ТОЛЬКО на русском языке.
2) Используй ТОЛЬКО сведения из контекста: формулировки, пункты, правила.
3) Если в контексте есть релевантная информация, используй её для ответа, даже если она не полная.
4) Если в контексте НЕТ достаточной информации для полного ответа, но есть частичная информация, ответь на основе имеющихся данных и укажи, что для полного ответа нужна дополнительная информация.
5) Только если в контексте вообще НЕТ релевантной информации, ответь: "Недостаточно данных в БЗ для точного ответа".
6) Для расчётных вопросов дай краткую формулу/шаги строго по тексту БЗ.
7) Не придумывай факты вне контекста.

ОТВЕТ (кратко, по делу):
"""

            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.chat_model
            
            model_output = chain.invoke({
                "context": context,
                "question": question
            })
            
            return model_output.content
            
        except Exception as e:
            return f"Ошибка получения ответа: {e}"
    
    def ask_question(self, question: str, context_limit: int = 3) -> Dict:
        """Ask a question and get response with context - compatibility method"""
        try:
            response = self.get_response_with_context(question, context_limit=context_limit)
            return {
                'answer': response,
                'sources': [],
                'context_used': context_limit
            }
        except Exception as e:
            return {
                'answer': f"Ошибка получения ответа: {e}",
                'sources': [],
                'context_used': 0
            }
    
    def set_chat_backend(self, provider: str, model: str, **kwargs):
        """Set chat backend - compatibility method"""
        # This method is kept for compatibility but the backend is set during initialization
        print(f"⚠️ set_chat_backend вызван, но backend уже установлен при инициализации")
    
    def get_available_kbs(self) -> Dict[int, Dict]:
        """Get information about available knowledge bases"""
        return self.kb_metadata.copy()
    
    def get_kb_stats(self) -> Dict:
        """Get statistics about loaded knowledge bases"""
        total_docs = sum(meta.get('doc_count', 0) for meta in self.kb_metadata.values())
        total_chunks = sum(meta.get('chunk_count', 0) for meta in self.kb_metadata.values())
        
        return {
            'total_kbs': len(self.kb_metadata),
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'kbs': self.kb_metadata
        }
