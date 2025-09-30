import os
import json
import time
import pytest


PROXYAPI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
MODEL_NAME = "gpt-4o"
TEST_QUESTION = "Расчет трафика за неполный месяц"


def require_api_key() -> str:
    key = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("PROXYAPI_KEY/PROXYAPI_API_KEY/OPENAI_API_KEY is not set; skipping external test")
    return key


@pytest.mark.timeout(15)
def test_proxyapi_chat_completions_quick_answer():
    """Smoke test: ProxyAPI chat/completions returns a short answer quickly."""
    import requests

    api_key = require_api_key()
    url = f"{PROXYAPI_BASE_URL}/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Отвечай кратко и по делу на русском."},
            {"role": "user", "content": TEST_QUESTION},
        ],
        "max_tokens": 200,
        "temperature": 0.2,
    }

    t0 = time.time()
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=10,
    )
    dt = time.time() - t0

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:500]}"
    data = resp.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    assert content and isinstance(content, str), f"Empty content: {data}"
    assert dt < 12, f"Response too slow: {dt:.2f}s"


@pytest.mark.timeout(15)
def test_proxyapi_openai_sdk_responses_quick_answer():
    """Smoke test via OpenAI SDK Responses API against ProxyAPI base_url."""
    try:
        from openai import OpenAI
    except Exception:
        pytest.skip("openai SDK not installed")

    api_key = require_api_key()
    client = OpenAI(api_key=api_key, base_url=PROXYAPI_BASE_URL)

    t0 = time.time()
    resp = client.responses.create(model=MODEL_NAME, input=TEST_QUESTION)
    dt = time.time() - t0

    text = getattr(resp, "output_text", None) or getattr(resp, "content", None) or str(resp)
    assert isinstance(text, str) and len(text.strip()) > 0
    assert dt < 12, f"SDK response too slow: {dt:.2f}s"



