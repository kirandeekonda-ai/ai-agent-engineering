# Module 1, Lesson 1.2: Pydantic Models - Type-Safe Data Structures

## 📚 What We're Learning Today

In Lesson 1.1, we returned simple dictionaries. But what if we need to:
- Accept data from users (like submitting an idea)?
- Ensure the data is valid (has required fields, correct types)?
- Provide clear documentation of what data we expect?

That's where **Pydantic** comes in!

---

## 🤔 The Problem with Plain Dictionaries

Imagine if someone sends this to our API:
```python
{
    "idea": "Automate reports",
    # Missing: description, time_estimate
    "cost": "five thousand"  # Should be a number!
}
```

With plain dictionaries, we'd have to write tons of validation code manually. Pydantic **does this automatically**.

---

## 🎯 What is Pydantic?

Think of Pydantic as a **blueprint** or **contract** for your data.

| Without Pydantic | With Pydantic |
|------------------|---------------|
| Hope the data is correct | Guaranteed correct structure |
| Manual validation everywhere | Automatic validation |
| No auto-completion in IDE | Full type hints |
| Bad error messages | Clear, helpful errors |

---

## 📝 How Pydantic Works

### 1. Define a Model (Blueprint)
```python
from pydantic import BaseModel

class Idea(BaseModel):
    title: str           # Must be a string
    description: str     # Must be a string
    time_estimate: int   # Must be an integer (weeks)
    cost_estimate: int   # Must be an integer (dollars)
```

### 2. FastAPI Uses It
```python
@app.post("/ideas")
def create_idea(idea: Idea):  # ← FastAPI knows to expect an Idea
    return {"received": idea.title}
```

### 3. What Happens Automatically
- ✅ Validates data types (string, int, etc.)
- ✅ Checks required fields exist
- ✅ Returns helpful error messages if invalid
- ✅ Updates the `/docs` page with the expected structure

---

## 🏗️ Real Example: Chat Message

For our chatbot, we need to receive messages from users:

```python
class ChatMessage(BaseModel):
    """
    A message in the conversation.
    """
    content: str                    # The actual message text
    session_id: str | None = None   # Optional: to track conversations
```

**Breaking it down:**
- `content: str` - Required field, must be a string
- `session_id: str | None = None` - Optional field (defaults to None)
- The docstring appears in the auto-generated docs

---

## 🔄 Response Models

We can also use Pydantic for **responses** (what we send back):

```python
class ChatResponse(BaseModel):
    message: str           # The bot's reply
    session_id: str        # So frontend knows which conversation
    timestamp: str         # When the message was sent
```

Then in our endpoint:
```python
@app.post("/chat", response_model=ChatResponse)
def chat(message: ChatMessage) -> ChatResponse:
    # FastAPI ensures we return the right structure
    return ChatResponse(
        message="Thanks for your idea!",
        session_id=message.session_id or "new",
        timestamp="2026-02-08T08:50:00"
    )
```

---

## 🎓 Key Concepts

| Concept | Explanation |
|---------|-------------|
| **BaseModel** | The parent class for all Pydantic models |
| **Type Hints** | `str`, `int`, `bool` tell Python what type to expect |
| **Optional Fields** | `field: str \| None = None` means it's not required |
| **Validation** | Happens automatically when FastAPI receives data |
| **Serialization** | Converting Python objects → JSON (automatic) |

---

## 🛠️ What We'll Build

We'll update `main.py` to:
1. Define a `ChatMessage` model
2. Define a `ChatResponse` model  
3. Create a `/chat` endpoint that uses both
4. Test it in `/docs`

Ready to code it?
