import os
import time


QUESTION = "Расчет трафика за неполный месяц"


def require_api_key() -> str:
    key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set PROXYAPI_KEY/PROXYAPI_API_KEY for this test")
    return key


def test_rag_with_proxyapi_generates_answer_quickly():
    from modules.rag.multi_kb_rag import MultiKBRAG

    api_key = require_api_key()

    rag = MultiKBRAG()
    # Switch to ProxyAPI GPT-4o for fast, concise answers
    rag.set_chat_backend(
        provider="proxyapi",
        model=os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"),
        base_url=os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
        api_key=api_key,
        temperature=float(os.getenv("PROXYAPI_TEMPERATURE", "0.2")),
    )

    t0 = time.time()
    result = rag.ask_question(QUESTION)
    dt = time.time() - t0

    assert isinstance(result, dict), "ask_question must return dict"
    answer = result.get("answer")
    assert answer and isinstance(answer, str) and len(answer.strip()) > 0, "Empty RAG answer"
    # Expect a short response (heuristic)
    assert dt < 15, f"RAG response too slow: {dt:.2f}s"



