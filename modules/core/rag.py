"""
RAG (Retrieval-Augmented Generation) module for satellite billing system
Contains functions for generating SQL queries from natural language
"""

import re
import sys
from typing import Optional
from openai import OpenAI
from .database import get_database_schema
from pathlib import Path

# Добавляем путь к базовому агенту
sys.path.append(str(Path(__file__).parent.parent.parent))
from modules.core.base_agent import BaseAgent
from config.settings import MODELS, OLLAMA_BASE_URL

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


class SQLAgent(BaseAgent):
    """SQL Agent для генерации SQL запросов из естественного языка"""
    
    def __init__(self):
        super().__init__("SQLAgent", "sql")
        self.client = OpenAI(base_url=self.ollama_base_url + "/v1", api_key="ollama")
    
    def update_model(self, new_model: str) -> bool:
        """Обновить модель SQL Agent"""
        # Проверяем, что модель поддерживает SQL генерацию
        if self._is_sql_compatible_model(new_model):
            self.model_name = new_model
            logger.info(f"SQL Agent переключен на модель {new_model}")
            return True
        else:
            logger.warning(f"Модель {new_model} не поддерживает SQL генерацию")
            return False
    
    def _is_sql_compatible_model(self, model: str) -> bool:
        """Проверить, поддерживает ли модель SQL генерацию"""
        # Список моделей, которые хорошо работают с SQL
        sql_compatible_models = [
            "qwen3:8b", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
            "llama3.1:8b", "llama3.1:70b", "llama3.2:3b", "llama3.2:11b",
            "codellama:7b", "codellama:13b", "codellama:34b",
            "deepseek-coder:6.7b", "deepseek-coder:33b",
            "sqlcoder:7b", "sqlcoder:15b"
        ]
        
        # Проверяем точное совпадение или частичное
        for compatible in sql_compatible_models:
            if model.lower() in compatible.lower() or compatible.lower() in model.lower():
                return True
        
        # Если модель не в списке, но содержит ключевые слова для SQL
        sql_keywords = ["sql", "code", "coder", "qwen", "llama", "deepseek"]
        return any(keyword in model.lower() for keyword in sql_keywords)
    
    def generate_sql_query(self, question: str, company: Optional[str] = None) -> str:
        """Генерировать SQL запрос из естественного языка с полной пост-обработкой"""
        try:
            # Добавляем контекст компании если указан
            company_context = f"for the company '{company}'" if company else "across all companies"
            
            # Получаем схему базы данных
            schema = get_database_schema()
            
            # Загружаем промпт-шаблон
            prompt = self._get_sql_prompt_template(schema, company_context, question)
            
            # Если компания не указана, добавляем инструкцию не фильтровать по компании
            if not company:
                prompt += "\n\nOPERATOR SCOPE: The question is across ALL companies. DO NOT add any filter by u.company."
            
            # Получаем модель из session_state или используем дефолтную
            try:
                import streamlit as st
                selected_model = st.session_state.get('sql_assistant_model', self.model_name)
            except:
                selected_model = self.model_name
            
            # Генерируем SQL запрос
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Применяем полную пост-обработку как в оригинале
            final_query = self._post_process_sql(raw_response, company)
            
            # Логируем использование токенов
            usage = response.usage
            if usage:
                self.log_usage(
                    provider="ollama",
                    model=self.model_name,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    question=question,
                    response_length=len(final_query)
                )
            
            return final_query
            
        except Exception as e:
            # Логируем ошибку
            self.log_usage(
                provider="ollama",
                model=self.model_name,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                question=question,
                response_length=0
            )
            return f"Ошибка генерации SQL: {e}"
    
    def _post_process_sql(self, query: str, company: Optional[str] = None) -> str:
        """Полная пост-обработка SQL запроса как в оригинале"""
        # Remove <think> blocks (qwen3:8b thinking format) - aggressive cleanup
        # Remove all <think>...</think> blocks (including nested ones)
        query = re.sub(r'<think>.*?</think>', '', query, flags=re.DOTALL)
        
        # Remove any remaining <think> tags without closing
        if "<think>" in query:
            think_start = query.find("<think>")
            query = query[:think_start].strip()
        
        # Remove any markdown formatting
        if query.startswith("```"):
            query = query.split("```")[1]
        if query.startswith("sql"):
            query = query[3:]
        if query.endswith("```"):
            query = query.rsplit("```", 1)[0]
        
        final_query = query.strip()
        
        # Post-process: if no company is specified, strip accidental filters like u.company = ''
        if not company:
            # Remove patterns WHERE/AND u.company = '' (with optional spaces/quotes)
            patterns = [
                r"\bWHERE\s+u\.company\s*=\s*''\s*AND\s*",
                r"\bAND\s+u\.company\s*=\s*''\s*",
                r"\bWHERE\s+u\.company\s*=\s*''\s*",
                r"\bWHERE\s+u\.company\s*=\s*\"\"\s*AND\s*",
                r"\bAND\s+u\.company\s*=\s*\"\"\s*",
                r"\bWHERE\s+u\.company\s*=\s*\"\"\s*",
            ]
            cleaned = final_query
            for pat in patterns:
                cleaned = re.sub(pat, lambda m: "WHERE " if "WHERE" in m.group(0) and "AND" in m.group(0) else "", cleaned, flags=re.IGNORECASE)
            # Clean possible trailing WHERE with no condition
            cleaned = re.sub(r"\bWHERE\s*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
            final_query = cleaned.strip()

        # Post-process: replace unsupported strftime('%Q') with computed quarter label
        try:
            # Replace strftime('%Y-%Q', <date_expr>) with 'YYYY-Qn'
            def repl_year_quarter(m):
                date_expr = m.group(1)
                return (
                    "(strftime('%Y', " + date_expr + ") || '-Q' || "
                    "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER))"
                )
            final_query = re.sub(r"strftime\('%Y-%Q',\s*(.*?)\)", repl_year_quarter, final_query)

            # Replace standalone strftime('%Q', <date_expr>) with quarter number 1..4
            def repl_quarter(m):
                date_expr = m.group(1)
                return (
                    "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER)"
                )
            final_query = re.sub(r"strftime\('%Q',\s*(.*?)\)", repl_quarter, final_query)

            # If someone labels quarter as just year, upgrade to proper YYYY-Qn
            # Pattern: strftime('%Y', <date_expr>) as quarter
            def repl_year_as_quarter(m):
                date_expr = m.group(1)
                return (
                    "(strftime('%Y', " + date_expr + ") || '-Q' || "
                    "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER)) as quarter"
                )
            final_query = re.sub(r"strftime\('%Y'\s*,\s*(.*?)\)\s+as\s+quarter", repl_year_as_quarter, final_query, flags=re.IGNORECASE)
        except Exception:
            pass

        # Heuristic fix: ensure grouping by service_type for traffic totals
        try:
            q = final_query
            # Trigger only if summing usage and querying billing_records
            if re.search(r"SUM\s*\(\s*\w*usage_amount\s*\)", q, re.IGNORECASE) and re.search(r"FROM\s+billing_records\s+\w+|FROM\s+billing_records\b", q, re.IGNORECASE):
                # Skip if service_type already present
                if not re.search(r"\bservice_type\b", q, re.IGNORECASE):
                    # Find alias for billing_records
                    m = re.search(r"FROM\s+billing_records\s+(\w+)", q, re.IGNORECASE)
                    alias = m.group(1) if m else "b"
                    # Ensure JOIN service_types exists
                    if not re.search(r"JOIN\s+service_types\s+st\b", q, re.IGNORECASE):
                        # Insert JOIN before WHERE or GROUP BY
                        if "WHERE" in q:
                            q = re.sub(r"\bWHERE\b", f"JOIN service_types st ON {alias}.service_type_id = st.id\nWHERE", q, count=1, flags=re.IGNORECASE)
                        elif "GROUP BY" in q:
                            q = re.sub(r"\bGROUP BY\b", f"JOIN service_types st ON {alias}.service_type_id = st.id\nGROUP BY", q, count=1, flags=re.IGNORECASE)
                        else:
                            q = q + f"\nJOIN service_types st ON {alias}.service_type_id = st.id"
                    # Inject st.name as service_type into SELECT
                    q = re.sub(r"SELECT\s+", "SELECT st.name as service_type, ", q, count=1, flags=re.IGNORECASE)
                    # Add st.name to GROUP BY if exists
                    if "GROUP BY" in q:
                        q = re.sub(r"GROUP BY\s+", "GROUP BY st.name, ", q, count=1, flags=re.IGNORECASE)
                    final_query = q
        except Exception:
            pass
 
        # Heuristic fix: normalize stray past years to CURRENT year where a year literal is used
        try:
            # Replace '2023'/'2024' single-year literals with strftime('%Y','now') comparisons when used with strftime('%Y', ...)
            # strftime('%Y', X) IN ('2023','2024') -> strftime('%Y', X) = strftime('%Y','now')
            final_query = re.sub(r"strftime\('\%Y',\s*([^)]+)\)\s+IN\s*\('\d{4}'(?:,\s*'\d{4}')*\)", r"strftime('%Y', \1) = strftime('%Y','now')", final_query, flags=re.IGNORECASE)
            # strftime('%Y', X) = '2023' -> strftime('%Y', X) = strftime('%Y','now')
            final_query = re.sub(r"strftime\('\%Y',\s*([^)]+)\)\s*=\s*'\d{4}'", r"strftime('%Y', \1) = strftime('%Y','now')", final_query, flags=re.IGNORECASE)
            # For monthly strings 'YYYY-MM' with old years, coerce to current month
            final_query = re.sub(r"strftime\('\%Y-\%m',\s*([^)]+)\)\s*=\s*'\d{4}-\d{2}'", r"strftime('%Y-%m', \1) = strftime('%Y-%m','now')", final_query, flags=re.IGNORECASE)
        except Exception:
            pass

        # Heuristic fix: if there is a YEAR filter but no monthly breakdown, add month grouping
        try:
            q = final_query
            # Detect billing_records presence and its alias
            m_from = re.search(r"FROM\s+billing_records\s+(\w+)|FROM\s+billing_records\b", q, re.IGNORECASE)
            br_alias = None
            if m_from:
                if m_from.group(1):
                    br_alias = m_from.group(1)
                else:
                    br_alias = 'b'
            if br_alias:
                # Check for a year filter on billing_date
                has_year_filter = re.search(r"strftime\('\%Y',\s*" + br_alias + r"\.billing_date\s*\)", q, re.IGNORECASE) is not None
                has_month_group = re.search(r"strftime\('\%Y-\%m',\s*" + br_alias + r"\.billing_date\s*\)", q, re.IGNORECASE) is not None
                if has_year_filter and not has_month_group:
                    # Inject month into SELECT
                    q = re.sub(r"SELECT\s+", "SELECT strftime('%Y-%m', " + br_alias + ".billing_date) as month, ", q, count=1, flags=re.IGNORECASE)
                    # Prepend month into GROUP BY if exists, else create it
                    if "GROUP BY" in q:
                        q = re.sub(r"GROUP BY\s+", "GROUP BY strftime('%Y-%m', " + br_alias + ".billing_date), ", q, count=1, flags=re.IGNORECASE)
                    else:
                        q += "\nGROUP BY strftime('%Y-%m', " + br_alias + ".billing_date)"
                    # Prefer ordering by month first if ORDER BY exists and no month
                    if "ORDER BY" in q and not re.search(r"\border\s+by[^\n]*month", q, re.IGNORECASE):
                        q = re.sub(r"ORDER BY\s+", "ORDER BY month, ", q, count=1, flags=re.IGNORECASE)
                    final_query = q
        except Exception:
            pass

        return final_query
    
    def _get_sql_prompt_template(self, schema: str, company_context: str, question: str) -> str:
        """Получить шаблон промпта для SQL генерации - точно как в оригинале"""
        return f"""You are a SQLite expert for a satellite communications billing system. Generate a query for the following question {company_context}.

CRITICAL RULES - DO NOT VIOLATE:
1. NEVER modify, simplify, or shorten the user's question
2. If user mentions "SBD" - ALWAYS filter by service_type = 'SBD'
3. If user mentions "by each device" or "per device" - ALWAYS include device details in SELECT and GROUP BY
4. If user mentions specific month (like "май" = May) - ALWAYS filter by that month
5. Preserve EVERY detail from the original question
6. Do NOT make assumptions or "improvements" to the user's request
7. If you need to interpret the question, add a comment in SQL explaining your understanding
8. NEVER change the user's intent - only translate it to SQL
9. If the user asks to show traffic (usage) totals, you MUST:
   - Include service_types.name as service_type and service_types.unit as unit in SELECT
   - Group by service_type (and unit) to avoid mixing different services
   - NEVER sum usage across different service types without grouping by service_type
10. DATE DEFAULTS: If the user does NOT specify a year or month, default to the CURRENT year/month based on SQLite now(). For example, for yearly scope use strftime('%Y', ...) = strftime('%Y', 'now'), for monthly scope use strftime('%Y-%m', ...) = strftime('%Y-%m', 'now').

{schema}

Key Information:
1. Date and Time:
   - Month format: strftime('%Y-%m', billing_date)
   - Last N months: date(billing_date) >= date('now', '-N months')
   - Current month: strftime('%Y-%m', billing_date) = strftime('%Y-%m', 'now')
   - IMPORTANT: Date filtering should be done in the main query, not in WHERE clause of CTEs

2. Traffic and Money:
   - Usage amounts are stored in usage_amount field (KB for SBD, MB for VSAT_DATA, minutes for VSAT_VOICE)
   - Monthly totals: GROUP BY strftime('%Y-%m', billing_date)
   - Money totals: ROUND(SUM(amount), 2)
   - Service types: SBD (KB), VSAT_DATA (MB), VSAT_VOICE (minutes)
   - IMPORTANT: Do NOT aggregate usage across different service types; always include st.name and st.unit in SELECT and GROUP BY when summing usage

3. Table Relationships:
   billing_records -> agreements (agreement_id)
   billing_records -> service_types (service_type_id)
   agreements -> users (user_id)
   agreements -> tariffs (tariff_id)
   tariffs -> service_types (service_type_id)
   devices -> users (user_id)
   sessions -> devices (imei)
   sessions -> service_types (service_type_id)

Example Query - Traffic by company and service type in last 3 months:
SELECT 
    strftime('%Y-%m', b.billing_date) as month,
    u.company,
    st.name as service_type,
    st.unit as unit,
    SUM(b.usage_amount) as total_usage,
    ROUND(SUM(b.amount), 2) as total_amount
FROM billing_records b
JOIN agreements a ON b.agreement_id = a.id
JOIN users u ON a.user_id = u.id
JOIN service_types st ON b.service_type_id = st.id
WHERE date(b.billing_date) >= date('now', '-3 months')
GROUP BY strftime('%Y-%m', b.billing_date), u.company, st.name, st.unit
ORDER BY month DESC, total_usage DESC;

Example Query - SBD traffic by each device for May 2025 (EXACTLY as user requested):
-- User asked for: "SBD трафик за май месяц по каждому устройству"
-- Understanding: Show SBD traffic for May 2025, grouped by each device
-- Preserving: SBD filter, May 2025 filter, device grouping
SELECT 
    d.imei as device_id,
    d.device_type,
    d.model,
    st.name as service_type,
    st.unit as unit,
    SUM(b.usage_amount) as total_usage,
    ROUND(SUM(b.amount), 2) as total_amount
FROM billing_records b
JOIN devices d ON b.imei = d.imei
JOIN users u ON d.user_id = u.id
JOIN service_types st ON b.service_type_id = st.id
WHERE u.company = '{{company}}'
    AND st.name = 'SBD'  -- User specifically asked for SBD
    AND strftime('%Y-%m', b.billing_date) = '2025-05'  -- User asked for May
GROUP BY d.imei, d.device_type, d.model, st.name, st.unit  -- User asked "by each device"
ORDER BY total_usage DESC;

REMEMBER: If user asks for "SBD трафик за май месяц по каждому устройству" - this EXACTLY means:
- Filter by service_type = 'SBD' 
- Filter by month = '2025-05'
- Group by device (imei, device_type, model)
- Show traffic per device

Question: {question}

IMPORTANT: 
- Return the SQL query with comments explaining how you understood the question
- Use -- for SQL comments
- NEVER modify the user's intent
- If user asks for "SBD" - include SBD filter
- If user asks "by each device" - include device grouping
- If user asks for specific month - include month filter

Return the SQL query with understanding comments:"""


# Создаем глобальный экземпляр SQL Agent
sql_agent = SQLAgent()


def generate_sql(question: str, company: Optional[str] = None) -> str:
    """Generate SQL query from natural language question using SQLAgent."""
    return sql_agent.generate_sql_query(question, company)

