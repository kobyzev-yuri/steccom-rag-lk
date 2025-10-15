"""
RAG (Retrieval-Augmented Generation) module for satellite billing system
Contains functions for generating SQL queries from natural language
"""

import re
from typing import Optional
from openai import OpenAI
from .database import get_database_schema
from pathlib import Path

# Initialize OpenAI client with ProxyAPI
import os
client = OpenAI(
    base_url=os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
    api_key=os.getenv("PROXYAPI_API_KEY", "")
)


def generate_sql(question: str, company: Optional[str] = None) -> str:
    """Generate SQL query from natural language question."""
    # DEBUG: Print the original question
    
    # Add company context if provided
    company_context = f"for the company '{company}'" if company else "across all companies"
    
    # Get current database schema
    schema = get_database_schema()
    
    # Load externalized prompt template if available
    default_prompt = """You are a SQLite expert for a satellite communications billing system. Generate a query for the following question {company_context}.

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
WHERE u.company = '{company}'
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

    prompt_path = Path("resources/prompts/sql_prompt.txt")
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        prompt = prompt_template.format(company=company or "", question=question)
    else:
        prompt = default_prompt

    # If no company is specified (operator across all companies), enforce instruction not to add company filter
    if not company:
        prompt += "\n\nOPERATOR SCOPE: The question is across ALL companies. DO NOT add any filter by u.company."

    # DEBUG: Print part of the prompt to verify it contains the rules

    # Get model from session state or use default
    import streamlit as st
    model = st.session_state.get('sql_assistant_model', 'qwen3:8b')
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Slight flexibility for better adaptation
        max_tokens=2000  # Limit response length to prevent infinite generation
    )
    
    raw_response = response.choices[0].message.content.strip()
    
    query = raw_response
    
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
        import re as _re
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
            cleaned = _re.sub(pat, lambda m: "WHERE " if "WHERE" in m.group(0) and "AND" in m.group(0) else "", cleaned, flags=_re.IGNORECASE)
        # Clean possible trailing WHERE with no condition
        cleaned = _re.sub(r"\bWHERE\s*$", "", cleaned, flags=_re.IGNORECASE | _re.MULTILINE)
        final_query = cleaned.strip()

    # Post-process: replace unsupported strftime('%Q') with computed quarter label
    try:
        import re as _re
        # Replace strftime('%Y-%Q', <date_expr>) with 'YYYY-Qn'
        def repl_year_quarter(m):
            date_expr = m.group(1)
            return (
                "(strftime('%Y', " + date_expr + ") || '-Q' || "
                "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER))"
            )
        final_query = _re.sub(r"strftime\('%Y-%Q',\s*(.*?)\)", repl_year_quarter, final_query)

        # Replace standalone strftime('%Q', <date_expr>) with quarter number 1..4
        def repl_quarter(m):
            date_expr = m.group(1)
            return (
                "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER)"
            )
        final_query = _re.sub(r"strftime\('%Q',\s*(.*?)\)", repl_quarter, final_query)

        # If someone labels quarter as just year, upgrade to proper YYYY-Qn
        # Pattern: strftime('%Y', <date_expr>) as quarter
        def repl_year_as_quarter(m):
            date_expr = m.group(1)
            return (
                "(strftime('%Y', " + date_expr + ") || '-Q' || "
                "CAST(((CAST(strftime('%m', " + date_expr + ") AS INTEGER)-1) / 3 + 1) AS INTEGER)) as quarter"
            )
        final_query = _re.sub(r"strftime\('%Y'\s*,\s*(.*?)\)\s+as\s+quarter", repl_year_as_quarter, final_query, flags=_re.IGNORECASE)
    except Exception:
        pass

    # Heuristic fix: ensure grouping by service_type for traffic totals
    try:
        import re as _re
        q = final_query
        # Trigger only if summing usage and querying billing_records
        if _re.search(r"SUM\s*\(\s*\w*usage_amount\s*\)", q, _re.IGNORECASE) and _re.search(r"FROM\s+billing_records\s+\w+|FROM\s+billing_records\b", q, _re.IGNORECASE):
            # Skip if service_type already present
            if not _re.search(r"\bservice_type\b", q, _re.IGNORECASE):
                # Find alias for billing_records
                m = _re.search(r"FROM\s+billing_records\s+(\w+)", q, _re.IGNORECASE)
                alias = m.group(1) if m else "b"
                # Ensure JOIN service_types exists
                if not _re.search(r"JOIN\s+service_types\s+st\b", q, _re.IGNORECASE):
                    # Insert JOIN before WHERE or GROUP BY
                    if "WHERE" in q:
                        q = _re.sub(r"\bWHERE\b", f"JOIN service_types st ON {alias}.service_type_id = st.id\nWHERE", q, count=1, flags=_re.IGNORECASE)
                    elif "GROUP BY" in q:
                        q = _re.sub(r"\bGROUP BY\b", f"JOIN service_types st ON {alias}.service_type_id = st.id\nGROUP BY", q, count=1, flags=_re.IGNORECASE)
                    else:
                        q = q + f"\nJOIN service_types st ON {alias}.service_type_id = st.id"
                # Inject st.name as service_type into SELECT
                q = _re.sub(r"SELECT\s+", "SELECT st.name as service_type, ", q, count=1, flags=_re.IGNORECASE)
                # Add st.name to GROUP BY if exists
                if "GROUP BY" in q:
                    q = _re.sub(r"GROUP BY\s+", "GROUP BY st.name, ", q, count=1, flags=_re.IGNORECASE)
                final_query = q
    except Exception:
        pass
 
    # Heuristic fix: normalize stray past years to CURRENT year where a year literal is used
    try:
        import re as _re
        # Replace '2023'/'2024' single-year literals with strftime('%Y','now') comparisons when used with strftime('%Y', ...)
        # strftime('%Y', X) IN ('2023','2024') -> strftime('%Y', X) = strftime('%Y','now')
        final_query = _re.sub(r"strftime\('\%Y',\s*([^)]+)\)\s+IN\s*\('\d{4}'(?:,\s*'\d{4}')*\)", r"strftime('%Y', \1) = strftime('%Y','now')", final_query, flags=_re.IGNORECASE)
        # strftime('%Y', X) = '2023' -> strftime('%Y', X) = strftime('%Y','now')
        final_query = _re.sub(r"strftime\('\%Y',\s*([^)]+)\)\s*=\s*'\d{4}'", r"strftime('%Y', \1) = strftime('%Y','now')", final_query, flags=_re.IGNORECASE)
        # For monthly strings 'YYYY-MM' with old years, coerce to current month
        final_query = _re.sub(r"strftime\('\%Y-\%m',\s*([^)]+)\)\s*=\s*'\d{4}-\d{2}'", r"strftime('%Y-%m', \1) = strftime('%Y-%m','now')", final_query, flags=_re.IGNORECASE)
    except Exception:
        pass

    # Heuristic fix: if there is a YEAR filter but no monthly breakdown, add month grouping
    try:
        import re as _re
        q = final_query
        # Detect billing_records presence and its alias
        m_from = _re.search(r"FROM\s+billing_records\s+(\w+)|FROM\s+billing_records\b", q, _re.IGNORECASE)
        br_alias = None
        if m_from:
            if m_from.group(1):
                br_alias = m_from.group(1)
            else:
                br_alias = 'b'
        if br_alias:
            # Check for a year filter on billing_date
            has_year_filter = _re.search(r"strftime\('\%Y',\s*" + br_alias + r"\.billing_date\s*\)", q, _re.IGNORECASE) is not None
            has_month_group = _re.search(r"strftime\('\%Y-\%m',\s*" + br_alias + r"\.billing_date\s*\)", q, _re.IGNORECASE) is not None
            if has_year_filter and not has_month_group:
                # Inject month into SELECT
                q = _re.sub(r"SELECT\s+", "SELECT strftime('%Y-%m', " + br_alias + ".billing_date) as month, ", q, count=1, flags=_re.IGNORECASE)
                # Prepend month into GROUP BY if exists, else create it
                if "GROUP BY" in q:
                    q = _re.sub(r"GROUP BY\s+", "GROUP BY strftime('%Y-%m', " + br_alias + ".billing_date), ", q, count=1, flags=_re.IGNORECASE)
                else:
                    q += "\nGROUP BY strftime('%Y-%m', " + br_alias + ".billing_date)"
                # Prefer ordering by month first if ORDER BY exists and no month
                if "ORDER BY" in q and not _re.search(r"\border\s+by[^\n]*month", q, _re.IGNORECASE):
                    q = _re.sub(r"ORDER BY\s+", "ORDER BY month, ", q, count=1, flags=_re.IGNORECASE)
                final_query = q
    except Exception:
        pass

    return final_query
