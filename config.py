import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = (
    os.getenv("OLLAMA_MODEL")
    or os.getenv("MODEL_NAME")
    or "llama3.2:3b"
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
