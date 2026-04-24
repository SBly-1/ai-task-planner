import os
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models import FakeListChatModel
from config import LLM_PROVIDER, OLLAMA_MODEL, OPENAI_MODEL

def get_llm():
    if LLM_PROVIDER == "mock":
        return FakeListChatModel(responses=[
            '{"intent":"help","task_data":{}}',
            '{"intent":"add_task","task_data":{"title":"Лаба","deadline":"2024-05-20","duration_minutes":60,"importance":"high","category":"study"}}',
            '{"intent":"show_plan","task_data":{}}'
        ])
    elif LLM_PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model=OPENAI_MODEL, temperature=0.3)
    else:
        return ChatOllama(model=OLLAMA_MODEL, temperature=0.3, base_url="http://localhost:11434")