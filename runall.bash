#!binbash
#

source .venv/bin/activate

streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
