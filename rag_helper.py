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
        """Load and parse steccom.json data"""
        try:
            json_path = Path("steccom.json")
            if not json_path.exists():
                # If file doesn't exist, return empty list to allow system to work with built-in docs
                print("Warning: steccom.json not found, using built-in documentation only")
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing steccom.json: {e}")
            return []
        except Exception as e:
            print(f"Warning: Error loading steccom.json: {e}")
            return []

    def process_json_to_documents(self, data: Union[List[Dict], List[str]]) -> List[Document]:
        """Convert JSON data into text documents with enhanced personal account focus"""
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
           - users: информация о пользователях
           - agreements: договоры и тарифы
           - devices: подключенные устройства
           - billing_records: записи о трафике и оплате
           
        2. ФОРМАТЫ ДАННЫХ:
           
           Даты: YYYY-MM-DD
           Время: HH:MM:SS
           Трафик: в байтах, конвертируется в ГБ
           Деньги: в рублях с двумя знаками после запятой
           
        3. ОГРАНИЧЕНИЯ СИСТЕМЫ:
           
           - Максимальный период запроса: 1 год
           - Максимальное количество записей: 10,000
           - Формат экспорта: только CSV
           - Язык интерфейса: только русский
           
        4. БЕЗОПАСНОСТЬ:
           
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
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": "steccom"}
                    ))
        
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
        1. agreements - filter: user_id IN (SELECT id FROM users WHERE company = '{company}')
           - id
           - user_id
           - plan_type
           - monthly_fee
           - traffic_limit_bytes
           - start_date
           - end_date
           - status
        
        2. devices - filter: user_id IN (SELECT id FROM users WHERE company = '{company}')
           - imei
           - user_id
           - device_type
           - model
           - activated_at
        
        3. billing_records - join through devices or agreements
           - id
           - agreement_id
           - imei
           - billing_date
           - traffic_bytes
           - amount
           - paid
           - payment_date
        
        4. users - used for company filtering
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
            a.plan_type as plan,
            a.monthly_fee as fee,
            a.start_date as start_date,
            a.end_date as end_date,
            a.status as status
        FROM agreements a
        JOIN users u ON a.user_id = u.id
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

    def get_response(self, question: str) -> str:
        """Get response for a question using RAG"""
        template = """Ты - эксперт по личному кабинету системы спутниковой связи СТЭККОМ. Твоя задача - помогать пользователям разобраться с работой системы.

КОНТЕКСТ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}

ПРАВИЛА ОТВЕТА:
1. Отвечай ТОЛЬКО на русском языке
2. Будь подробным, но кратким
3. Если вопрос о том, как что-то сделать - дай пошаговую инструкцию
4. Если вопрос о возможностях системы - перечисли основные функции
5. Если вопрос о примерах запросов - приведи конкретные примеры
6. Если вопрос о проблемах - предложи решения
7. Если не знаешь ответа - честно скажи об этом
8. Используй информацию из контекста
9. Не выдумывай информацию

СТРУКТУРА ОТВЕТА:
- Краткий ответ на вопрос
- Пошаговые инструкции (если применимо)
- Примеры (если применимо)
- Дополнительные советы (если применимо)

ОТВЕТ:"""

        prompt = ChatPromptTemplate.from_template(template)
        
        try:
            # Get relevant documents
            relevant_docs = self.vectorstore.as_retriever().get_relevant_documents(question)
            
            # Format documents into context
            context = self.format_docs(relevant_docs)
            
            # Create and run the chain
            chain = prompt | self.chat_model | StrOutputParser()
            
            # Run the chain with both context and question
            response = chain.invoke({
                "context": context,
                "question": question
            })
            
            return response
        except Exception as e:
            return f"Ошибка получения ответа: {e}"

    def search_similar(self, query: str, k: int = 3) -> List[str]:
        """Search for similar documents"""
        if not self.vectorstore:
            return ["Vectorstore not initialized"]
            
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs] 