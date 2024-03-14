"""
Phospho internal configuration file
"""

import os

BASE_URL = "https://api.phospho.ai/v2"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# Custom LLM provider setup
USE_OLLAMA = os.environ.get("USE_OLLAMA", False)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", None)
