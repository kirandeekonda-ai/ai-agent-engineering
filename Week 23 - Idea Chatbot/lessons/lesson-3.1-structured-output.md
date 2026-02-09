# Module 3, Lesson 3.1: Structured Output - Getting JSON from LLMs

## 📚 What We're Learning Today

So far, the AI responds with **text**. But we need **structured data** - title, description, time estimate, cost, etc. This lesson teaches how to get **JSON** from the LLM.

---

## 🤔 The Challenge

**Current:**
```
User: "I want to build an API to automate reports. It would save 5 hours per week."
AI: "That sounds great! Tell me more..."
```

**Goal:**
```json
{
  "title": "Report Automation API",
  "description": "Build an API to automate weekly report generation",
  "time_saved": "5 hours/week",
  "estimated_cost": "$5,000-$10,000",
  "resources_needed": ["2 developers", "API infrastructure"],
  "complexity": "medium"
}
```

---

## 🎯 How to Get Structured Output

### Method 1: Prompt Engineering (What we'll use)
Ask the LLM to return JSON in the system prompt:

```python
prompt = """
Extract the idea from this conversation and return ONLY valid JSON:
{
  "title": "...",
  "description": "..."
}
"""
```

✅ Works with all models  
✅ Flexible  
❌ Not guaranteed to be valid JSON

### Method 2: JSON Schema Mode (Groq supports this!)
Some models support guaranteed JSON output.

---

## 🏗️ Our Extraction Logic

When should we extract an idea?
1. User clicks "Submit Idea" button (Module 5)
2. OR after enough context is gathered (automatic)

**For now:** We'll add a `/extract` endpoint that analyzes a session and extracts the idea.

---

## 📝 The Extraction Prompt

```python
EXTRACTION_PROMPT = """
Analyze this conversation and extract a structured idea summary.

Return ONLY valid JSON (no markdown, no explanation):
{
  "title": "Short title (max 10 words)",
  "description": "Clear 2-3 sentence description",
  "problem_solved": "What problem does it solve?",
  "time_estimate": "Development time estimate",
  "cost_estimate": "Cost range or 'Unknown'",
  "resources_needed": ["resource1", "resource2"],
  "impact": "Who benefits and how?"
}

If information is missing, use "Not specified" for that field.
"""
```

---

## 🛠️ Implementation Steps

1. Add `extract_idea()` method to `GroqClient` (uses llama-4-scout model)
2. Create `/extract` endpoint in FastAPI
3. Test it with conversation history

Ready to build the extraction system?
