import streamlit as st
import os
import sys
from pathlib import Path

# Гарантируем, что путь kb_admin находится в PYTHONPATH при запуске из app.py
kb_admin_dir = Path(__file__).parents[2]
if str(kb_admin_dir) not in sys.path:
    sys.path.append(str(kb_admin_dir))

from kb_admin.config.settings import SETTINGS

def render_settings_page():
    st.header("⚙️ Настройки системы")

    st.subheader("Пути")
    p = SETTINGS["paths"]
    st.write(f"UPLOAD_DIR: `{p['UPLOAD_DIR']}`")
    st.write(f"ARCHIVE_DIR: `{p['ARCHIVE_DIR']}`")
    st.write(f"PROCESSED_DIR: `{p['PROCESSED_DIR']}`")

    with st.expander("🔎 Диагностика PATH env"):
        st.code(
            "\n".join([
                f"STEC_FORCE_LOCAL_DIRS={os.getenv('STEC_FORCE_LOCAL_DIRS', '')}",
                f"STEC_UPLOAD_DIR={os.getenv('STEC_UPLOAD_DIR', '')}",
                f"STEC_ARCHIVE_DIR={os.getenv('STEC_ARCHIVE_DIR', '')}",
                f"STEC_PROCESSED_DIR={os.getenv('STEC_PROCESSED_DIR', '')}",
                f"UPLOAD_DIR={os.getenv('UPLOAD_DIR', '')}",
                f"ARCHIVE_DIR={os.getenv('ARCHIVE_DIR', '')}",
                f"PROCESSED_DIR={os.getenv('PROCESSED_DIR', '')}",
            ]),
            language="bash"
        )

    st.subheader("Модели")
    m = SETTINGS["models"]
    st.write(f"VISION_MODEL: `{m['VISION_MODEL']}`")
    st.write(f"CHAT_MODEL: `{m['CHAT_MODEL']}`")

    st.subheader("DOCX")
    d = SETTINGS["docx"]
    st.write(f"ENABLE_AI_CLEANING_TEXT: {d['ENABLE_AI_CLEANING_TEXT']}")
    st.write(f"ABSTRACT_ENABLED: {d['ABSTRACT_ENABLED']}")
    st.write(f"QA_SKIP_ABSTRACT: {d['QA_SKIP_ABSTRACT']}")
    st.write(f"HUGE_MB_THRESHOLD: {d['HUGE_MB_THRESHOLD']}")
    st.write(f"HUGE_CHARS_THRESHOLD: {d['HUGE_CHARS_THRESHOLD']}")

    # Проверка поддержки DOCX
    try:
        import docx  # noqa: F401
        st.success("python-docx: доступен")
    except Exception as e:
        st.error(f"python-docx: недоступен ({e})")

    st.info("Меняйте значения через переменные окружения (STEC_*) и перезапускайте веб‑приложение.")
