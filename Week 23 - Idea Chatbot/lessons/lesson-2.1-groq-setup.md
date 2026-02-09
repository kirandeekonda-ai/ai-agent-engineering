# Module 2, Lesson 2.1: Groq Client Setup - Multi-Model Strategy

## 📚 What We're Learning Today

Now that we have a working API, it's time to connect the **brain** - the LLM (Large Language Model). We'll use Groq's API with a smart multi-model strategy to avoid rate limits.

---

## 🤔 Why Multiple Models?

Remember our earlier discussion? Groq's free tier has token limits per model. Instead of exhausting one model, we'll use **different models for different tasks**:

| Task | Model | Why |
|------|-------|-----|
| **Conversational Chat** | `llama-3.1-8b-instant` | Fast, efficient (14.4K RPD) |
| **Idea Extraction** | `llama-4-scout-17b-16e-instruct` | Better reasoning (30K TPM) |
| **Quality Check** | `llama-guard-4-12b` | Designed for evaluation (15K TPM) |

**Benefits:**
- ✅ Spread load across models → avoid hitting limits
- ✅ Use the right tool for each job
- ✅ Better results (specialized models)

---

## 🏗️ Architecture

```
User Message
    ↓
FastAPI Endpoint
    ↓
GroqClient (decides which model)
    ↓
    ├─→ chat() → llama-3.1-8b-instant
    ├─→ extract_idea() → llama-4-scout
    └─→ evaluate() → llama-guard
    ↓
Response back to user
```

---

## 📝 The Groq Client Class

We'll create a `GroqClient` class with different methods for different tasks:

```python
class GroqClient:
    """Multi-model client for Groq API"""
    
    MODELS = {
        "chat": "llama-3.1-8b-instant",
        "extract": "meta-llama/llama-4-scout-17b-16e-instruct",
        "evaluate": "meta-llama/llama-guard-4-12b"
    }
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
    
    def chat(self, message, conversation_history):
        # Use fast model for conversation
        pass
    
    def extract_idea(self, conversation):
        # Use reasoning model for extraction
        pass
```

---

## 🔑 Environment Variables

We'll store the API key securely using environment variables:

**Create `.env` file:**
```
GROQ_API_KEY=your_api_key_here
```

**Load it in Python:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
```

**Why `.env`?**
- ✅ Keep secrets out of code
- ✅ Different keys for dev/production
- ✅ Never commit API keys to Git

---

## 🛠️ What We'll Build

1. Create `llm_client.py` with the `GroqClient` class
2. Implement the `chat()` method
3. Update `main.py` to use the real LLM
4. Test the integration

**Dependencies needed:**
```bash
pip install groq python-dotenv
```

Ready to connect the AI brain?
