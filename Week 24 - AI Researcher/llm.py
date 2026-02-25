import os
from openai import OpenAI
from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai

# Load .env from root folder
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Groq client via OpenAI-compatible API, wrapped for LangSmith tracing
client = wrap_openai(OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
))

def call_model(model: str, system: str, user: str, temperature: float = 0.3) -> str:
    """
    Generic LLM caller. All agents use this so model routing is centralised.

    Args:
        model:       Groq model ID e.g. "llama-3.1-8b-instant"
        system:      System prompt (agent's role/instructions)
        user:        User-facing prompt content
        temperature: Sampling temperature (lower = more deterministic)

    Returns:
        Raw string content from the model response.
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
    )
    return completion.choices[0].message.content
