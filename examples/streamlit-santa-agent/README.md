# Streamlit + phospho example

This is an example of a Santa Claus chatbot, implemented with phospho and streamlit.

## Local deployment

Create `secrets.toml` in the `.streamlit` folder. 

```toml
OPENAI_API_KEY=...
PHOSPHO_PROJECT_ID=...
PHOSPHO_API_KEY=...
```

You need an OpenAI key and a phospho account. 

Run the frontend the following way:

```bash
cd streamlit-agent # Make sure you are in this repository
streamlit run frontend.py
```
