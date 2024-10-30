"""
Phospho internal configuration file
"""

import os

BASE_URL = "https://api.phospho.ai/v2"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# Optional: Set this environment variable to instead use an Ollama model everywhere
OVERRIDE_WITH_OLLAMA_MODEL = os.getenv("OVERRIDE_WITH_OLLAMA_MODEL", None)
