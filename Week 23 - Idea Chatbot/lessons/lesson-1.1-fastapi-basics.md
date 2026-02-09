# Module 1, Lesson 1.1: FastAPI Basics - Your First API Endpoint

## 📚 What We're Learning Today

Today you'll learn the fundamentals of FastAPI - a modern Python web framework. By the end of this lesson, you'll understand:
- What an API is and why we need one
- How FastAPI works
- How to create your first endpoint
- How to test it in the browser

---

## 🤔 Concept: What is an API?

Think of an API (Application Programming Interface) as a **waiter in a restaurant**:

| Restaurant | Our App |
|------------|---------|
| You (customer) | Frontend (chat UI in browser) |
| Menu | Available endpoints |
| Waiter | API |
| Kitchen | Backend logic (LLM, database) |

You tell the waiter your order → Waiter brings it to kitchen → Kitchen prepares → Waiter brings back food.

Similarly: Frontend sends request → API receives → Backend processes → API sends response.

---

## 🎯 Why FastAPI?

| Feature | Why It Matters |
|---------|----------------|
| **Fast** | Built on modern async Python |
| **Auto Documentation** | Creates interactive API docs automatically |
| **Type Safety** | Catches errors before they happen |
| **Easy to Learn** | Clean, simple syntax |

---

## 🏗️ Architecture Overview

```
Browser (Frontend)
    ↓ HTTP Request
FastAPI Server (What we're building now)
    ↓
Backend Logic (LLM, Database - later modules)
```

---

## 📝 The Code - Explained Line by Line

We'll create `main.py` - the entry point for our API.

### Import Statement
```python
from fastapi import FastAPI
```
**What it does**: Imports the FastAPI class (the core of the framework)
**Why**: We need this to create our API application

### Create the App
```python
app = FastAPI()
```
**What it does**: Creates an instance of FastAPI (our app)
**Why**: This `app` object is where we'll define all our endpoints

### Define an Endpoint
```python
@app.get("/")
```
**What it does**: This is a "decorator" that tells FastAPI "when someone visits the `/` route with a GET request, run the function below"
**Why**: The `@` syntax is Python's way of adding functionality to functions

### The Function
```python
def root():
    return {"message": "Idea Assistant API"}
```
**What it does**: Returns a dictionary (Python will automatically convert to JSON)
**Why**: This is what the browser/frontend sees when they call this endpoint

---

## 🛠️ Let's Build It

I'll create the file now, and we'll test it together.

**Questions before we proceed:**
1. Do you understand the waiter analogy?
2. Any questions about the code structure?

Once you're ready, I'll create the file and show you how to run it!
