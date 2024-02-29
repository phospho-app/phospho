# FastAPI + phospho example

This is an example of a Santa Claus chatbot, implemented with phospho, a fastapi backend, and a streamlit frontend.

## Local deployment

Create `.env` at the root of the folder. 

```txt
OPENAI_API_KEY=...
PHOSPHO_PROJECT_ID=...
PHOSPHO_API_KEY=...
```

You need an OpenAI key and a phospho account. 

Run the backend server:

```bash
cd fastapi-streamlit-agent # Make sure you are in this repository
uvicorn backend:app --reload
```

Run the frontend the following way:

```bash
streamlit run frontend.py
```

