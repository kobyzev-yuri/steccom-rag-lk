import json
from typing import List, Dict, Tuple, Union
from pathlib import Path
import numpy as np
import os
import warnings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.schema import Document

class RAGHelper:
    def __init__(self):
        # Suppress deprecation warnings from legacy providers used only here
        try:
            from langchain_core._api.deprecation import LangChainDeprecationWarning
            warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
        except Exception:
            warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Embeddings: use a local SentenceTransformer adapter to avoid torch_dtype issues
        embedding_model = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
        device = os.getenv("EMBEDDING_DEVICE", "cpu")

        class LocalHFEmbeddings:
            def __init__(self, model_name: str, device: str = "cpu", normalize: bool = True):
                self.model = SentenceTransformer(model_name, device=device)
                self.normalize = normalize

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                if not texts:
                    return []
                vectors = self.model.encode(
                    texts,
                    normalize_embeddings=self.normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=32,
                )
                return vectors.tolist()

            def embed_query(self, text: str) -> List[float]:
                vectors = self.model.encode(
                    [text],
                    normalize_embeddings=self.normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=1,
                )
                return vectors[0].tolist()

        self.embeddings = LocalHFEmbeddings(embedding_model, device=device, normalize=True)
        print(f"🔧 RAGHelper embeddings: provider=sentence-transformers model={embedding_model} device={device}")

        # Chat model (kept as Ollama unless overridden in the main app)
        self.chat_model = ChatOllama(model=os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b"))
        self.vectorstore = None
        self.documents = []
        self.initialize_vectorstore()

    def load_json_data(self) -> Union[List[Dict], List[str]]:
        """Load and parse steccom.json and optional docs/kb/*.json files"""
        try:
            aggregated: List[Union[Dict, str]] = []

            # Primary KB file at project root
            json_path = Path("steccom.json")
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    aggregated.extend(data)
                elif isinstance(data, dict) or isinstance(data, str):
                    aggregated.append(data)
            else:
                print("Warning: steccom.json not found, relying on built-in docs and docs/kb/")

            # Additional KB files under docs/kb/*.json
            kb_dir = Path("docs/kb")
            if kb_dir.exists() and kb_dir.is_dir():
                for kb_file in sorted(kb_dir.glob("*.json")):
                    try:
                        with open(kb_file, 'r', encoding='utf-8') as f:
                            kb_data = json.load(f)
                        if isinstance(kb_data, list):
                            for it in kb_data:
                                if isinstance(it, dict):
                                    it = {**it, "_kb_file": str(kb_file)}
                                aggregated.append(it)
                        elif isinstance(kb_data, dict) or isinstance(kb_data, str):
                            if isinstance(kb_data, dict):
                                kb_data = {**kb_data, "_kb_file": str(kb_file)}
                            aggregated.append(kb_data)
                        print(f"Loaded KB file: {kb_file}")
                    except Exception as e:
                        print(f"Warning: failed to load KB file {kb_file}: {e}")

            return aggregated
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing steccom.json: {e}")
            return []
        except Exception as e:
            print(f"Warning: Error loading steccom.json: {e}")
            return []

    def process_json_to_documents(self, data: Union[List[Dict], List[str]]) -> List[Document]:
        """Convert JSON data into text documents with enhanced personal account focus.
        Honors optional metadata fields: audience (user/admin), scope (current_billing/legacy_billing), status.
        """
        documents = []
        
        # NOTE: Built-in guide/examples/troubleshooting/technical removed.
        # They must now live in docs/kb/*.json and will be loaded via load_json_data.
        
        # Process original documentation if available
        if isinstance(data, list) and data:
            for item in data:
                content = ""
                if isinstance(item, dict):
                    # Handle dictionary items
                    content += f"Title: {item.get('title', '')}\n"
                    content += f"Description: {item.get('description', '')}\n"
                    
                    if 'content' in item and isinstance(item['content'], list):
                        for section in item['content']:
                            if isinstance(section, dict):
                                content += f"\nSection: {section.get('title', '')}\n"
                                content += f"{section.get('text', '')}\n"
                                
                                if 'subsections' in section and isinstance(section['subsections'], list):
                                    for subsection in section['subsections']:
                                        if isinstance(subsection, dict):
                                            content += f"\nSubsection: {subsection.get('title', '')}\n"
                                            content += f"{subsection.get('text', '')}\n"
                elif isinstance(item, str):
                    # Handle string items
                    content = item
                
                if content.strip():
                    metadata: Dict = {"source": "steccom"}
                    if isinstance(item, dict):
                        # propagate role/scope metadata if present
                        if 'audience' in item:
                            metadata['audience'] = item['audience']
                        if 'scope' in item:
                            metadata['scope'] = item['scope']
                        if 'status' in item:
                            metadata['status'] = item['status']
                        if '_kb_file' in item:
                            metadata['kb_file'] = item['_kb_file']
                        if 'title' in item:
                            metadata['title'] = item['title']
                    documents.append(Document(page_content=content, metadata=metadata))
        
        return documents

    def initialize_vectorstore(self):
        """Initialize FAISS vectorstore with documents"""
        try:
            json_data = self.load_json_data()
            documents = self.process_json_to_documents(json_data)
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            chunks = text_splitter.split_documents(documents)
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            self.documents = documents
            print("RAG system initialized successfully with", len(documents), "documents")
            
        except Exception as e:
            print(f"Error initializing vectorstore: {e}")
            raise

    def format_docs(self, docs: List[Document]) -> str:
        """Format documents into a single string context"""
        return "\n\n".join(doc.page_content for doc in docs)

    def get_query_suggestion(self, user_question: str, company: str) -> Tuple[str, str]:
        """Generate SQL query suggestion based on user question and company"""
        template = """You are a SQL expert helping users create queries to analyze their company data.
        User can only see data for their company ({company}).
        
        Available tables and constraints:
        1. service_types - types of services
           - id
           - name (SBD, VSAT_DATA, VSAT_VOICE)
           - unit (KB, MB, minutes)
           - description
        
        2. tariffs - tariff plans
           - id
           - service_type_id
           - name
           - price_per_unit
           - monthly_fee
           - traffic_limit
           - is_active
        
        3. agreements - filter: user_id IN (SELECT id FROM users WHERE company = '{company}')
           - id
           - user_id
           - tariff_id
           - start_date
           - end_date
           - status
        
        4. devices - filter: user_id IN (SELECT id FROM users WHERE company = '{company}')
           - imei
           - user_id
           - device_type
           - model
           - activated_at
        
        5. sessions - usage sessions
           - id
           - imei
           - service_type_id
           - session_start
           - session_end
           - usage_amount
        
        6. billing_records - join through devices or agreements
           - id
           - agreement_id
           - imei
           - service_type_id
           - billing_date
           - usage_amount
           - amount
           - paid
           - payment_date
        
        7. users - used for company filtering
           - id
           - username
           - company
           - role
        
        Important rules:
        1. Use only English names for column aliases
        2. Use short table aliases (a for agreements, d for devices, etc.)
        3. Always qualify column names with table aliases
        4. Format dates as YYYY-MM-DD
        5. Use simple quotes for string values
        6. Never use Russian text in SQL
        7. For company filtering, always join with users table
        8. Return ONLY the SQL query, no explanations or thinking
        
        Example query for current agreement:
        SELECT 
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
        WHERE u.company = '{company}'
            AND date('now') BETWEEN date(a.start_date) AND date(a.end_date)
            AND a.status = 'active';
        
        User question: {question}
        
        Return ONLY the SQL query for SQLite, no explanations, no thinking, just the query:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        chain = prompt | self.chat_model | StrOutputParser()
        
        try:
            response = chain.invoke({"question": user_question, "company": company})
            
            # Clean the response from thinking and explanations
            query = self.clean_sql_response(response)
            
            # Generate explanation separately
            explanation = self.generate_explanation(user_question, query, company)
            
            return query, explanation
        except Exception as e:
            return "", f"Ошибка генерации запроса: {e}"

    def clean_sql_response(self, response: str) -> str:
        """Clean SQL response from thinking and explanations"""
        # Remove thinking blocks
        if "<think>" in response and "</think>" in response:
            start = response.find("</think>") + len("</think>")
            response = response[start:].strip()
        
        # Remove markdown code blocks
        if "```sql" in response:
            response = response.split("```sql")[1]
        if "```" in response:
            response = response.split("```")[0]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "QUERY:", "SQL:", "SELECT", "WITH", "INSERT", "UPDATE", "DELETE"
        ]
        
        # Find the actual SQL query
        lines = response.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts with SQL keywords
            if any(line.upper().startswith(prefix) for prefix in prefixes_to_remove):
                in_sql = True
                sql_lines.append(line)
            elif in_sql and (line.startswith(';') or line.endswith(';')):
                sql_lines.append(line)
                break
            elif in_sql:
                sql_lines.append(line)
        
        if sql_lines:
            return '\n'.join(sql_lines)
        
        # If no SQL found, return the original response cleaned
        return response.strip()

    def generate_explanation(self, question: str, query: str, company: str) -> str:
        """Generate explanation for the SQL query"""
        template = """Объясни этот SQL запрос на русском языке:

ВОПРОС: {question}
SQL ЗАПРОС: {query}
КОМПАНИЯ: {company}

Объяснение должно быть кратким и понятным, описывать что делает запрос и какие таблицы использует."""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.chat_model | StrOutputParser()
        
        try:
            explanation = chain.invoke({
                "question": question,
                "query": query,
                "company": company
            })
            return explanation
        except Exception as e:
            return f"Объяснение недоступно: {e}"

    def _load_prompt(self, path: str, default: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return default

    def _filter_docs_by_role_and_scope(self, docs: List[Document], role: str) -> List[Document]:
        filtered: List[Document] = []
        for doc in docs:
            audience = doc.metadata.get('audience') if isinstance(doc.metadata, dict) else None
            scope = doc.metadata.get('scope') if isinstance(doc.metadata, dict) else None

            # role filter: if audience present, only include if role is allowed
            if audience:
                try:
                    allowed = set(audience)
                except Exception:
                    allowed = {str(audience)}
                if role == 'user' and 'user' not in allowed:
                    continue
                if role == 'admin' and 'admin' not in allowed and 'user' in allowed:
                    # admins can also read user docs
                    pass
            # else: no audience -> include for all

            # always include both scopes but mark legacy later
            filtered.append(doc)
        return filtered

    def _mark_legacy_in_context(self, docs: List[Document]) -> str:
        blocks: List[str] = []
        for doc in docs:
            is_legacy = False
            scope = doc.metadata.get('scope') if isinstance(doc.metadata, dict) else None
            if scope and ('legacy_billing' in scope if isinstance(scope, list) else scope == 'legacy_billing'):
                is_legacy = True
            prefix = "[LEGACY] " if is_legacy else ""
            blocks.append(prefix + doc.page_content)
        return "\n\n".join(blocks)

    def get_response(self, question: str, role: str = 'user') -> str:
        """Get response for a question using RAG with role-based filtering and legacy marking"""
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        default_prompt = (
            "Ты - эксперт по личному кабинету системы спутниковой связи СТЭККОМ. Твоя задача - помогать пользователям разобраться с работой системы.\n\n"
            "КОНТЕКСТ:\n{context}\n\nРОЛЬ ПОЛЬЗОВАТЕЛЯ: {role}\n\nПРАВИЛА ОТВЕТА:\n1. Отвечай ТОЛЬКО на русском языке\n2. Будь подробным, но кратким\n3. Если вопрос о том, как что-то сделать - дай пошаговую инструкцию\n"
            "4. Если вопрос о возможностях системы - перечисли актуальные функции текущего личного кабинета\n5. Если вопрос о примерах запросов - приведи конкретные примеры\n6. Если вопрос о проблемах - предложи решения\n7. Если не знаешь ответа - честно скажи об этом\n"
            "8. Используй информацию из контекста\n9. Не выдумывай информацию\n10. Материалы по наследной/старой системе помечай как [LEGACY]. Если пользователь явно спрашивает про старую систему/регламент/бланк заказа — отвечай на основе [LEGACY] материалов и прямо укажи, что ответ относится к старой системе.\n\n"
            "СТРУКТУРА ОТВЕТА:\n- Краткий ответ на вопрос\n- Пошаговые инструкции (если применимо)\n- Примеры (если применимо)\n- Дополнительные советы (если применимо)\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}\n\nОТВЕТ:"
        )
        template = self._load_prompt("resources/prompts/assistant_prompt.txt", default_prompt)
        prompt = ChatPromptTemplate.from_template(template)

        try:
            # Detect legacy intent early to tune retrieval
            legacy_intent = False
            try:
                ql = question.lower()
                legacy_intent = any(k in ql for k in [
                    'старой системе', 'старая система', 'legacy', 'регламент', 'бланк заказа',
                    'старый регламент', 'устаревш'
                ])
            except Exception:
                legacy_intent = False

            # Retrieve and filter documents by role (increase k for legacy intent)
            base_k = 12 if not legacy_intent else 20
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": base_k})
            relevant_docs = retriever.get_relevant_documents(question)
            # If legacy intent and no legacy docs surfaced, do a targeted second pass
            if legacy_intent and not any(
                ('legacy_billing' in (d.metadata.get('scope') or [])) if isinstance(d.metadata.get('scope'), list)
                else (d.metadata.get('scope') == 'legacy_billing') for d in relevant_docs if isinstance(d.metadata, dict)
            ):
                probe_query = question + " legacy регламент бланк заказа common services"
                try:
                    extra = self.vectorstore.similarity_search(probe_query, k=10)
                    # merge without duplicates
                    seen_ids = set(id(doc) for doc in relevant_docs)
                    for doc in extra:
                        if id(doc) not in seen_ids:
                            relevant_docs.append(doc)
                            seen_ids.add(id(doc))
                except Exception:
                    pass

            # Ensure inclusion of specific legacy common services reg if user asks about бланк заказа/регламент
            if legacy_intent:
                try:
                    seen_ids = set(id(doc) for doc in relevant_docs)
                    for doc in self.documents:
                        meta = doc.metadata if isinstance(doc.metadata, dict) else {}
                        kb_file = (meta.get('kb_file') or '').lower()
                        title = (meta.get('title') or '').lower()
                        if 'legacy_reglament_commonservices' in kb_file or 'общие услуги' in title or 'common services' in title:
                            if id(doc) not in seen_ids:
                                relevant_docs.append(doc)
                                seen_ids.add(id(doc))
                except Exception:
                    pass
            relevant_docs = self._filter_docs_by_role_and_scope(relevant_docs, role)

            # If пользователь явно спрашивает про "бланк заказа" — принудительно добавим релевантные куски
            try:
                if legacy_intent and ('бланк заказа' in ql):
                    extra_snippets: List[Document] = []
                    for doc in self.documents:
                        meta = doc.metadata if isinstance(doc.metadata, dict) else {}
                        kb_file = (meta.get('kb_file') or '').lower()
                        if 'legacy_reglament_commonservices' in kb_file and 'бланк заказа' in doc.page_content.lower():
                            extra_snippets.append(doc)
                    if extra_snippets:
                        # Препендим, чтобы они были в контексте первыми
                        relevant_docs = extra_snippets + relevant_docs
            except Exception:
                pass

            # Format documents with legacy marking
            context = self._mark_legacy_in_context(relevant_docs)

            if legacy_intent:
                # Augment instructions inline
                template = template + "\n\nДОПОЛНЕНИЕ: Пользователь спрашивает про старую/наследную систему. Используй [LEGACY] материалы как основной источник ответа и явно пометь применимость."
                prompt = ChatPromptTemplate.from_template(template)

            chain = prompt | self.chat_model | StrOutputParser()
            
            # Add timeout protection for LLM call using threading
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def run_chain():
                try:
                    response = chain.invoke({
                        "context": context,
                        "question": question,
                        "role": role
                    })
                    result_queue.put(response)
                except Exception as e:
                    exception_queue.put(e)
            
            # Start the chain in a separate thread
            thread = threading.Thread(target=run_chain)
            thread.daemon = True
            thread.start()
            
            try:
                # Wait for result with 30 second timeout
                response = result_queue.get(timeout=30)
                
                elapsed = time.time() - start_time
                if elapsed > 10:
                    logger.warning(f"Slow RAG request: {elapsed:.1f}s for question: {question[:50]}...")
                
            except queue.Empty:
                elapsed = time.time() - start_time
                logger.error(f"RAG request timeout after {elapsed:.1f}s for question: {question[:50]}...")
                return self._get_fallback_response(question, role)
            except Exception as e:
                # Check if there's an exception from the thread
                try:
                    thread_exception = exception_queue.get_nowait()
                    e = thread_exception
                except queue.Empty:
                    pass
                
                elapsed = time.time() - start_time
                logger.error(f"RAG request failed after {elapsed:.1f}s: {e}")
                return self._get_fallback_response(question, role)
            
            # Build citations from filtered documents
            citations: List[str] = []
            seen = set()
            for doc in relevant_docs:
                meta = doc.metadata if isinstance(doc.metadata, dict) else {}
                key = (meta.get('kb_file'), meta.get('title'), meta.get('source'))
                if key in seen:
                    continue
                seen.add(key)
                is_legacy = False
                scope = meta.get('scope')
                if scope and ('legacy_billing' in scope if isinstance(scope, list) else scope == 'legacy_billing'):
                    is_legacy = True
                prefix = "[LEGACY] " if is_legacy else ""
                title = meta.get('title') or "KB документ"
                kb_file = meta.get('kb_file') or meta.get('source') or ""
                citations.append(f"- {prefix}{title} ({kb_file})")
                if len(citations) >= 5:
                    break

            if citations:
                response += "\n\n---\n**Источники:**\n" + "\n".join(citations)
            return response
        except Exception as e:
            logger.error(f"RAG system error: {e}")
            return self._get_fallback_response(question, role)
    
    def _get_fallback_response(self, question: str, role: str) -> str:
        """Fallback response when RAG system fails or times out"""
        return f"""Извините, система временно недоступна. 

**Краткий ответ:**
Для получения помощи по личному кабинету СТЭККОМ обратитесь в техническую поддержку.

**Контакты:**
- Телефон: +7 (495) 363-91-41
- Email: noc@steccom.ru
- Время работы: 24/7

**Основные функции ЛК:**
- Стандартные отчеты по трафику и устройствам
- Пользовательские SQL-запросы
- Просмотр договоров и тарифов

Попробуйте переформулировать вопрос или обратитесь к администратору."""

    def search_similar(self, query: str, k: int = 3) -> List[str]:
        """Search for similar documents"""
        if not self.vectorstore:
            return ["Vectorstore not initialized"]
            
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs] 