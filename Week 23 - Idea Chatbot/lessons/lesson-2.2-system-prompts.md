# Module 2, Lesson 2.2: System Prompts - Teaching the AI Its Role

## 📚 What We're Learning Today

Right now, the AI responds to your messages, but it doesn't have **personality** or **purpose**. System prompts are how we teach the AI what its job is.

---

## 🤔 What is a System Prompt?

Think of a system prompt as **instructions for an actor**:

| Without System Prompt | With System Prompt |
|----------------------|-------------------|
| Generic chatbot | Idea coach with a mission |
| Answers questions | Guides users to articulate ideas |
| No context | Knows it's for team innovation |

**Example:**
- **User:** "I have an idea"
- **Without system prompt:** "That's great! What is it?"
- **With system prompt:** "Excellent! Let me help you refine that. What problem does it solve, and who benefits?"

---

## 🎯 Our System Prompt Strategy

Based on your original requirements, the AI should:
1. **Encourage** idea sharing (not judge)
2. **Ask clarifying questions** (time, cost, resources)
3. **Help articulate** vague ideas into clear ones
4. **Stay focused** on workplace innovation

---

## 📝 The System Prompt

```python
SYSTEM_PROMPT = """You are an Idea Assistant for a company's innovation program.

Your role:
- Help employees articulate their ideas clearly
- Ask thoughtful questions about time savings, cost, and resources
- Be encouraging and supportive (never dismiss ideas)
- Guide users to think through implementation details

Guidelines:
- Keep responses concise (2-3 sentences max)
- Focus on one question at a time
- Be conversational and friendly
- If an idea is vague, help make it concrete

Remember: Your job is to coach, not to evaluate."""
```

---

## 🏗️ How System Messages Work in Chat API

Chat APIs use a **messages array** with different roles:

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant..."},  # Instructions to AI
    {"role": "user", "content": "Hello!"},                           # User's message
    {"role": "assistant", "content": "Hi! How can I help?"}          # AI's response
]
```

**Role types:**
- `system` - Instructions/personality (invisible to user)
- `user` - Messages from the human
- `assistant` - Messages from the AI

---

## 🛠️ Implementation

We'll update `llm_client.py` to:
1. Add the system prompt constant
2. Include it in every API call
3. Make it configurable for different tasks

Ready to give your AI a personality?
