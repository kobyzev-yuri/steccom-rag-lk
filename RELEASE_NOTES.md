# Release r2025.09 (Demo)

## Summary
- RAG: role-based filtering (user/admin)
- Legacy content marking: [LEGACY] for non-current billing materials
- Source citations appended to assistant answers
- Prompts externalized to `resources/prompts/`
- UI passes role to assistant; no breaking changes to Streamlit flows
- KB loader reads `docs/kb/*.json`

## User Impact
- Assistant answers now grounded in current LK capabilities with clear legacy separation and sources
- Standard reports and custom SQL flows unchanged

## Files of interest
- `modules/rag/rag_helper.py`
- `modules/core/rag.py`
- `modules/ui/ui_components.py`
- `resources/prompts/assistant_prompt.txt`
- `resources/prompts/sql_prompt.txt`
- `docs/kb/*.json`

## Next (separate branch)
- FastAPI backend (REST) for data, reports, and assistant
- Unit and contract tests (pytest, schemathesis)
