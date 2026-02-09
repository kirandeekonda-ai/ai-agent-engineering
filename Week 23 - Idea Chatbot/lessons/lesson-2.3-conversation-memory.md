# Module 2, Lesson 2.3: Multi-turn Conversations - Memory and Context

## 📚 What We're Learning Today

Right now, every message is treated as a **fresh conversation**. The AI doesn't remember what you said before. Let's fix that!

---

## 🤔 The Problem

**Current behavior:**
```
User: "I want to build a mobile app"
AI: "Great! What will it do?"

User: "It should track expenses"
AI: "What kind of expenses?" ❌ (Forgot about the mobile app!)
```

**Desired behavior:**
```
User: "I want to build a mobile app"
AI: "Great! What will it do?"

User: "It should track expenses"
AI: "A mobile expense tracker sounds useful! What features would it need?" ✅
```

---

## 🏗️ How Conversation Memory Works

LLMs are **stateless** - they don't remember anything. We need to send the **entire conversation history** with each request:

```python
messages = [
    {"role": "system", "content": "You are an idea assistant..."},
    {"role": "user", "content": "I want to build a mobile app"},
    {"role": "assistant", "content": "Great! What will it do?"},
    {"role": "user", "content": "It should track expenses"},  # Current message
]
```

Each time, we send **all** previous messages so the AI has context.

---

## 📦 Storage Strategy

We need to store conversation history **per session**. Two approaches:

### Approach 1: In-Memory (Simple, for learning)
```python
# Store in RAM (lost on server restart)
conversations = {
    "session-123": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
```
✅ Simple to implement  
❌ Lost on restart  
❌ Doesn't scale

### Approach 2: Database (Production-ready)
Store in SQLite/PostgreSQL (Module 4)  
✅ Persistent  
✅ Scales  
❌ More complex

**For now, we'll use Approach 1** (in-memory). We'll upgrade to database in Module 4.

---

## 🛠️ Implementation Plan

1. Create a `ConversationManager` class to track sessions
2. Update the `/chat` endpoint to use conversation history
3. Update the frontend to send `session_id` with each request
4. Test multi-turn conversations

---

## 🎯 Expected Outcome

After this lesson:
- ✅ AI remembers previous messages in a session
- ✅ Conversations feel natural
- ✅ Context is maintained throughout the chat

Ready to give your AI memory?
