"""
RAG (Retrieval-Augmented Generation) module for satellite billing system
Contains functions for generating SQL queries from natural language
"""

import re
from typing import Optional
from openai import OpenAI
from .database import get_database_schema
from pathlib import Path

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def generate_sql(question: str, company: Optional[str] = None) -> str:
    """Generate SQL query from natural language question."""
    # DEBUG: Print the original question
    print(f"🔍 DEBUG: Original question: '{question}'")
    
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

    # DEBUG: Print part of the prompt to verify it contains the rules
    print(f"🔍 DEBUG: Prompt contains 'NEVER modify': {'NEVER modify' in prompt}")
    print(f"🔍 DEBUG: Prompt contains 'SBD filter': {'SBD filter' in prompt}")

    response = client.chat.completions.create(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Slight flexibility for better adaptation
        max_tokens=2000  # Limit response length to prevent infinite generation
    )
    
    raw_response = response.choices[0].message.content.strip()
    print(f"🔍 DEBUG: Raw LLM response: '{raw_response[:200]}...'")
    
    query = raw_response
    
    # Remove <think> blocks (qwen3:8b thinking format) - aggressive cleanup
    # Remove all <think>...</think> blocks (including nested ones)
    query = re.sub(r'<think>.*?</think>', '', query, flags=re.DOTALL)
    
    # Remove any remaining <think> tags without closing
    if "<think>" in query:
        think_start = query.find("<think>")
        query = query[:think_start].strip()
        print(f"🔍 DEBUG: After removing incomplete <think>: '{query[:200]}...'")
    
    print(f"🔍 DEBUG: After removing <think> blocks: '{query[:200]}...'")
    
    # Remove any markdown formatting
    if query.startswith("```"):
        query = query.split("```")[1]
    if query.startswith("sql"):
        query = query[3:]
    if query.endswith("```"):
        query = query.rsplit("```", 1)[0]
    
    final_query = query.strip()
    print(f"🔍 DEBUG: Final SQL query: '{final_query[:200]}...'")
    print(f"🔍 DEBUG: Contains 'SBD': {'SBD' in final_query}")
    
    return final_query
