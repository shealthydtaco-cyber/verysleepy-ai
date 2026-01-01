API server

This small FastAPI app exposes a single endpoint to query the assistant:

POST /query
Body: { "input": "user question", "mode": "optional model mode" }
Response: { "response": "assistant text" }

Local dev:

1. Create a virtualenv and install deps:
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

2. Run the API:
   python api.py

The server will start on http://localhost:8000 (change `origins` in `api.py` if your frontend runs on a different port).
