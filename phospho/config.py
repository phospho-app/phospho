"""
Phospho internal configuration file
"""

import os

BASE_URL = "https://api.phospho.ai/v2"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
