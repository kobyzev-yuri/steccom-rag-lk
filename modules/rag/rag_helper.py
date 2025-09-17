import json
from typing import List, Dict, Tuple, Union
from pathlib import Path
import numpy as np
import os
import warnings
from langchain_huggingface import HuggingFaceEmbeddings
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

        # Embeddings: prefer multilingual HuggingFace
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "hf").lower()
        if embedding_provider in ("hf", "huggingface"):
            embedding_model = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        else:
            # Fallback to Ollama embeddings if explicitly requested
            from langchain_community.embeddings import OllamaEmbeddings
            self.embeddings = OllamaEmbeddings(model=os.getenv("OLLAMA_EMBED_MODEL", "all-minilm"))

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
        
        # Add comprehensive personal account usage guide
        lk_guide = """
        Личный кабинет - Полное руководство пользователя:
        
        1. ОСНОВНЫЕ ВОЗМОЖНОСТИ ЛИЧНОГО КАБИНЕТА:
           
           Анализ трафика:
           - Просмотр статистики потребления трафика по дням, неделям, месяцам
           - Анализ трафика по устройствам
           - Сравнение трафика за разные периоды
           - Выявление пиковых нагрузок
           
           Управление договорами:
           - Просмотр текущих договоров и их условий
           - Информация о тарифных планах
           - История договоров
           - Сроки действия договоров
           
           Мониторинг устройств:
           - Список всех подключенных устройств
           - Статус устройств (активные/неактивные)
           - Информация о моделях и типах устройств
           - История активации устройств
        
        2. КАК РАБОТАТЬ С ОТЧЕТАМИ:
           
           Стандартные отчеты:
           - Выберите тип отчета из выпадающего списка
           - Нажмите "Показать отчет"
           - Результаты отображаются в таблице
           - Можно скачать отчет в формате CSV
           
           Пользовательские запросы:
           - Задайте вопрос на русском языке
           - Система автоматически создаст SQL-запрос
           - Покажет объяснение запроса
           - Выведет результаты в таблице
        
        3. ПРИМЕРЫ ВОПРОСОВ ДЛЯ АНАЛИЗА:
           
           Трафик:
           - "Покажи мой трафик за последний месяц"
           - "Сколько трафика было вчера?"
           - "Дни с максимальным трафиком за неделю"
           - "Сравни трафик за январь и февраль"
           
           Устройства:
           - "Список всех моих устройств"
           - "Когда установили последнее устройство?"
           - "Сколько у меня активных устройств?"
           - "Покажи устройства по типам"
           
           Договоры:
           - "Информация о текущем договоре"
           - "Когда заканчивается договор?"
           - "Какая у меня абонентская плата?"
           - "История всех договоров"
        
        4. ОГРАНИЧЕНИЯ СИСТЕМЫ:
           
           - Доступны только данные вашей компании
           - Некоторые сложные запросы могут требовать уточнения
           - При ошибках попробуйте переформулировать вопрос
           - Система работает только с историческими данными
           
        5. ПОЛУЧЕНИЕ ПОМОЩИ:
           
           - Используйте помощника в левой панели
           - Задавайте вопросы о работе системы
           - Просматривайте примеры запросов
           - Обращайтесь к технической поддержке при проблемах
        """
        documents.append(Document(page_content=lk_guide, metadata={"source": "guide"}))
        
        # Add detailed query examples
        query_examples = """
        ПОДРОБНЫЕ ПРИМЕРЫ ЗАПРОСОВ К СИСТЕМЕ:
        
        1. АНАЛИЗ ТРАФИКА:
           
           Простые запросы:
           ✓ "Покажи мой трафик за вчера"
           ✓ "Сколько трафика было в прошлом месяце?"
           ✓ "Дни с максимальным трафиком за последний месяц"
           ✓ "Сравни трафик по неделям"
           
           Сложные запросы:
           ✓ "Покажи дни с превышением среднего трафика"
           ✓ "Сравни использование трафика по месяцам"
           ✓ "Найди периоды максимальной нагрузки"
           ✓ "Проанализируй тренд потребления трафика"
           ✓ "График потребления трафика за год"
        
        2. ИНФОРМАЦИЯ ОБ УСТРОЙСТВАХ:
           
           Базовые запросы:
           ✓ "Какие у меня установлены устройства?"
           ✓ "Когда установили последнее устройство?"
           ✓ "Список устройств по типам"
           ✓ "Устройства старше 2 лет"
           
           Аналитические запросы:
           ✓ "Сколько устройств каждого типа?"
           ✓ "Устройства, установленные в прошлом году"
           ✓ "Активные устройства за последний месяц"
           ✓ "Статистика по моделям устройств"
        
        3. ДОГОВОРЫ И ОПЛАТА:
           
           Информационные запросы:
           ✓ "Информация о текущем договоре"
           ✓ "Когда заканчивается договор?"
           ✓ "Сумма оплаты по договору"
           ✓ "История изменения абонентской платы"
           
           Аналитические запросы:
           ✓ "Сравни стоимость разных тарифов"
           ✓ "Покажи все мои договоры"
           ✓ "Анализ расходов по месяцам"
        
        4. КОМПЛЕКСНЫЙ АНАЛИЗ:
           
           Сравнительные запросы:
           ✓ "Сравни трафик до и после установки нового устройства"
           ✓ "Покажи статистику по дням недели"
           ✓ "Найди аномалии в трафике за последний месяц"
           ✓ "Средний трафик по месяцам"
           
           Прогнозные запросы:
           ✓ "Тренд потребления трафика"
           ✓ "Прогноз расходов на следующий месяц"
           ✓ "Анализ сезонности трафика"
        """
        documents.append(Document(page_content=query_examples, metadata={"source": "examples"}))
        
        # Add troubleshooting guide
        troubleshooting = """
        РУКОВОДСТВО ПО УСТРАНЕНИЮ ПРОБЛЕМ:
        
        1. ЧАСТЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ:
           
           Система не отвечает:
           - Проверьте подключение к интернету
           - Обновите страницу браузера
           - Очистите кэш браузера
           - Попробуйте другой браузер
           
           Ошибки в запросах:
           - Переформулируйте вопрос проще
           - Используйте примеры из списка
           - Проверьте правильность формулировки
           - Обратитесь к помощнику
           
           Нет данных:
           - Проверьте, что выбран правильный период
           - Убедитесь, что данные есть в системе
           - Попробуйте другой период времени
           
        2. КАК ПОЛУЧИТЬ ПОМОЩЬ:
           
           - Используйте помощника в левой панели
           - Задайте вопрос о проблеме
           - Опишите, что именно не работает
           - Приложите скриншот ошибки
           
        3. КОНТАКТЫ ПОДДЕРЖКИ:
           
           Телефон: +7 (495) 363-91-41
           Email: noc@steccom.ru
           Время работы: 24/7
        """
        documents.append(Document(page_content=troubleshooting, metadata={"source": "troubleshooting"}))
        
        # Add technical details
        technical_info = """
        ТЕХНИЧЕСКАЯ ИНФОРМАЦИЯ О СИСТЕМЕ:
        
        1. СТРУКТУРА ДАННЫХ:
           
           Таблицы в базе данных:
           - users: информация о пользователях (id, username, password, company, role)
           - service_types: типы услуг (id, name, unit, description)
           - tariffs: тарифы (id, service_type_id, name, price_per_unit, monthly_fee, traffic_limit)
           - agreements: договоры (id, user_id, tariff_id, start_date, end_date, status)
           - devices: подключенные устройства (imei, user_id, device_type, model, activated_at)
           - sessions: сессии использования (id, imei, service_type_id, session_start, session_end, usage_amount)
           - billing_records: записи о трафике и оплате (id, agreement_id, imei, service_type_id, billing_date, usage_amount, amount, paid)
           
        2. ТИПЫ УСЛУГ:
           
           - SBD: Short Burst Data (единица измерения: KB)
           - VSAT_DATA: VSAT Data (единица измерения: MB) 
           - VSAT_VOICE: VSAT Voice (единица измерения: minutes)
           
        3. ФОРМАТЫ ДАННЫХ:
           
           Даты: YYYY-MM-DD
           Время: HH:MM:SS
           Трафик: usage_amount в соответствующих единицах (KB/MB/minutes)
           Деньги: в рублях с двумя знаками после запятой
           
        4. СВЯЗИ ТАБЛИЦ:
           
           billing_records -> agreements (agreement_id)
           billing_records -> service_types (service_type_id)
           agreements -> users (user_id)
           agreements -> tariffs (tariff_id)
           tariffs -> service_types (service_type_id)
           devices -> users (user_id)
           sessions -> devices (imei)
           sessions -> service_types (service_type_id)
           
        5. ОГРАНИЧЕНИЯ СИСТЕМЫ:
           
           - Максимальный период запроса: 1 год
           - Максимальное количество записей: 10,000
           - Формат экспорта: только CSV
           - Язык интерфейса: только русский
           
        6. БЕЗОПАСНОСТЬ:
           
           - Доступ только к данным своей компании
           - Автоматическое логирование действий
           - Шифрование передаваемых данных
           - Регулярное резервное копирование
        """
        documents.append(Document(page_content=technical_info, metadata={"source": "technical"}))
        
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
        default_prompt = (
            "Ты - эксперт по личному кабинету системы спутниковой связи СТЭККОМ. Твоя задача - помогать пользователям разобраться с работой системы.\n\n"
            "КОНТЕКСТ:\n{context}\n\nРОЛЬ ПОЛЬЗОВАТЕЛЯ: {role}\n\nПРАВИЛА ОТВЕТА:\n1. Отвечай ТОЛЬКО на русском языке\n2. Будь подробным, но кратким\n3. Если вопрос о том, как что-то сделать - дай пошаговую инструкцию\n"
            "4. Если вопрос о возможностях системы - перечисли актуальные функции текущего личного кабинета\n5. Если вопрос о примерах запросов - приведи конкретные примеры\n6. Если вопрос о проблемах - предложи решения\n7. Если не знаешь ответа - честно скажи об этом\n"
            "8. Используй информацию из контекста\n9. Не выдумывай информацию\n10. Явно помечай материалы по наследной/старой системе как [LEGACY] и поясняй, что они не относятся к текущему ЛК\n\n"
            "СТРУКТУРА ОТВЕТА:\n- Краткий ответ на вопрос\n- Пошаговые инструкции (если применимо)\n- Примеры (если применимо)\n- Дополнительные советы (если применимо)\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}\n\nОТВЕТ:"
        )
        template = self._load_prompt("resources/prompts/assistant_prompt.txt", default_prompt)
        prompt = ChatPromptTemplate.from_template(template)

        try:
            # Retrieve and filter documents by role
            relevant_docs = self.vectorstore.as_retriever().get_relevant_documents(question)
            relevant_docs = self._filter_docs_by_role_and_scope(relevant_docs, role)

            # Format documents with legacy marking
            context = self._mark_legacy_in_context(relevant_docs)

            chain = prompt | self.chat_model | StrOutputParser()
            response = chain.invoke({
                "context": context,
                "question": question,
                "role": role
            })
            
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
            return f"Ошибка получения ответа: {e}"

    def search_similar(self, query: str, k: int = 3) -> List[str]:
        """Search for similar documents"""
        if not self.vectorstore:
            return ["Vectorstore not initialized"]
            
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs] 