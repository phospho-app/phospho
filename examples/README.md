# Examples

This folder contains demos, tutorials, and guides about how to leverage the phospho python module.

## Phospho lab

The phospho lab is the local version of phospho analytics.

- [Quickstart](./lab/quickstart.ipynb) How to run the Event detection pipeline on a dataset and optimize the pipeline
- [Create a Custom Job](./lab/custom-job.ipynb) How to create a custom job and run it with phospho lab
- [Parallel calls to OpenAI on a dataset](./lab/parallel-calls.ipynb) How to run parallel calls to OpenAI on a dataset with parallelization, while respecting rate limits

## Agent examples

These agents show how to log tasks to the phospho hosted version.

The phospho hosted version leverages the lab to run analytics on every logged message.

- [streamlit_santa_agent](./agents/streamlit_santa_agent) A Santa Claus agent in a sync streamlitwebapp
- [fastapi_streamlit_santa_agent](./agents/fastapi_streamlit_santa_agent) A fun Santa Claus agent with an async FastAPI backend and Streamlit frontend
- [langchain](./agents/langchain) Example of how the integration of phospho logging to a RAG Langchain agent.
- [ollama](./agents/ollama.py) Example of a GPT-like assistant working a model deployed locally with [Ollama](https://ollama.ai).
- [streamlit_assistant.py](./agents/streamlit_assistant.py) ChatGPT-like assistant displayed in a streamlit webapp

## Logging

These examples show basic functionalities of phospho logging.

- [hello.py](./logging/hello.py) How to log an OpenAI call
- [session.py](./logging/session.py) How to set up custom session management
- [metadata.py](./logging/session.py) How to log metadata
