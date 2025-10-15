"""
KB Admin RAG System
RAG система для работы с базами знаний KB Admin через JSON файлы
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

class KBAdminRAG:
    def __init__(self, kb_admin_path: str = None,
                 chat_provider: Optional[str] = None,
                 chat_model: Optional[str] = None,
                 proxy_base_url: Optional[str] = None,
                 proxy_api_key: Optional[str] = None,
                 temperature: float = 0.2):
        
        if kb_admin_path is None:
            # Используем абсолютный путь к KB Admin
            current_dir = Path(__file__).parent
            self.kb_admin_path = current_dir.parent.parent / "kb_admin"
        else:
            self.kb_admin_path = Path(kb_admin_path)
        
        # Путь к JSON файлам KB Admin
        self.json_kb_path = self.kb_admin_path / "docs" / "kb"
        
        # Embeddings backend: default to HuggingFace multilingual model
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
        if embedding_provider in ("hf", "huggingface") and HUGGINGFACE_AVAILABLE:
            embedding_model = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
            self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
            print(f"✅ Используем HuggingFace embeddings: {embedding_model}")
        else:
            # Fallback to Ollama embeddings
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
                'base_url': proxy_url, 'temperature': resolved_temperature
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
        
        self.vectorstores = {}  # kb_id -> vectorstore
        self.kb_metadata = {}   # kb_id -> metadata
        self.kb_chunks = {}     # kb_id -> List[Document]
        
        # Загружаем все активные базы знаний при инициализации
        try:
            self.load_all_kb_admin_kbs()
        except Exception as e:
            print(f"⚠️ Не удалось загрузить базы знаний KB Admin: {e}")

    def get_chat_backend_info(self) -> Dict:
        """Возвращает текущую конфигурацию LLM провайдера для RAG."""
        try:
            return dict(self._chat_backend)
        except Exception:
            return {"provider": "unknown"}

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
                model=model,
                openai_api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
                temperature=temperature
            )
            self._chat_backend = {
                'provider': 'openai', 'model': model, 'temperature': temperature
            }
        else:
            self.chat_model = ChatOllama(model=model, timeout=10)
            self._chat_backend = {'provider': 'ollama', 'model': model}

    def load_all_active_kbs(self) -> int:
        """Load all active knowledge bases - compatibility method"""
        return self.load_all_kb_admin_kbs()
    
    def load_all_kb_admin_kbs(self) -> int:
        """Load all KB Admin knowledge bases from JSON files"""
        if not self.json_kb_path.exists():
            print(f"⚠️ Директория KB Admin не найдена: {self.json_kb_path}")
            return 0
        
        loaded_count = 0
        json_files = list(self.json_kb_path.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                kb_info = kb_data.get('kb_info', {})
                kb_id = kb_info.get('id')
                
                if kb_id and self.load_kb_from_json(kb_id, kb_data):
                    loaded_count += 1
                    
            except Exception as e:
                print(f"⚠️ Ошибка загрузки KB из {json_file}: {e}")
        
        print(f"✅ Загружено активных БЗ из KB Admin: {loaded_count}")
        return loaded_count

    def load_kb_from_json(self, kb_id: int, kb_data: Dict) -> bool:
        """Load knowledge base from JSON data"""
        try:
            kb_info = kb_data.get('kb_info', {})
            documents = kb_data.get('documents', [])
            
            if not documents:
                print(f"⚠️ KB {kb_id} не содержит документов")
                return False
            
            # Создаем документы для обработки
            documents_list = []
            for doc in documents:
                # metadata может быть строкой JSON или объектом
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
            
            # Создаем чанки
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            chunks = []
            for doc in documents_list:
                chunks.extend(text_splitter.split_documents([doc]))
            
            # Создаем векторное хранилище
            vectorstore = FAISS.from_documents(chunks, self.embeddings)
            
            # Сохраняем данные
            self.vectorstores[kb_id] = vectorstore
            self.kb_metadata[kb_id] = {
                'name': kb_info.get('name', f'KB {kb_id}'),
                'description': kb_info.get('description', ''),
                'category': kb_info.get('category', ''),
                'doc_count': len(documents),
                'chunk_count': len(chunks)
            }
            self.kb_chunks[kb_id] = chunks
            
            print(f"✅ Загружена KB {kb_id}: {kb_info.get('name', '')} - {len(documents)} документов, {len(chunks)} чанков")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки KB {kb_id}: {e}")
            return False

    def search_across_kbs(self, query: str, kb_ids: List[int] = None, k: int = 5) -> List[Document]:
        """Search across multiple knowledge bases"""
        if not self.vectorstores:
            return []
        
        all_results = []
        search_kbs = kb_ids if kb_ids else list(self.vectorstores.keys())
        
        for kb_id in search_kbs:
            if kb_id in self.vectorstores:
                try:
                    results = self.vectorstores[kb_id].similarity_search(query, k=k)
                    all_results.extend(results)
                except Exception as e:
                    print(f"⚠️ Ошибка поиска в KB {kb_id}: {e}")
        
        # Сортируем по релевантности и возвращаем топ k
        return all_results[:k]

    def search(self, query: str, kb_names: Optional[List[str]] = None, limit: int = 5) -> List[Dict]:
        """Search in knowledge bases - API wrapper"""
        try:
            # Convert kb_names to kb_ids if provided
            kb_ids = None
            if kb_names:
                kb_ids = []
                for kb_name in kb_names:
                    for kb_id, metadata in self.kb_metadata.items():
                        if metadata.get('name') == kb_name:
                            kb_ids.append(kb_id)
                            break
            
            # Search across knowledge bases
            docs = self.search_across_kbs(query, kb_ids, k=limit)
            
            # Convert to API format
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "kb_id": doc.metadata.get('kb_id', 'Unknown'),
                    "kb_name": doc.metadata.get('kb_name', 'Unknown'),
                    "kb_category": doc.metadata.get('kb_category', 'Unknown')
                })
            
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def _format_documents(self, docs: List[Document]) -> str:
        """Format documents for context"""
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
            
            # Extract text content
            response_text = getattr(model_output, 'content', None) or str(model_output)
            
            return response_text
            
        except Exception as e:
            return f"Ошибка получения ответа: {e}"

    def get_available_kbs(self) -> List[Dict]:
        """Get list of available knowledge bases"""
        return [
            {
                'kb_id': kb_id,
                'name': metadata['name'],
                'description': metadata['description'],
                'category': metadata['category'],
                'doc_count': metadata['doc_count'],
                'chunk_count': metadata['chunk_count']
            }
            for kb_id, metadata in self.kb_metadata.items()
        ]

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

    def get_kb_statistics(self) -> Dict:
        """Get statistics about loaded knowledge bases"""
        total_docs = sum(metadata['doc_count'] for metadata in self.kb_metadata.values())
        total_chunks = sum(metadata['chunk_count'] for metadata in self.kb_metadata.values())
        
        return {
            'loaded_kbs': len(self.vectorstores),
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'kb_details': self.get_available_kbs()
        }
