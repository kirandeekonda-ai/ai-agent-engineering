# Module 1, Lesson 1.3: CORS - Connecting Frontend to Backend

## 📚 What We're Learning Today

You've built a beautiful frontend (`prototype-chat.html`) and a working backend API (`main.py`). But if you try to make them talk to each other right now, you'll hit an error:

```
Access to fetch at 'http://localhost:8000/chat' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

This lesson explains **what CORS is** and **how to fix it**.

---

## 🤔 The Problem: Browser Security

### The Restaurant Analogy

Imagine:
- Your **frontend** is a restaurant customer
- Your **backend** is the kitchen
- The **browser** is a security guard

The security guard has a rule: *"You can only order from kitchens on the same street!"*

- Frontend running on `http://localhost:3000` (one street)
- Backend running on `http://localhost:8000` (different street)
- Browser blocks the request! 🚫

This is called the **Same-Origin Policy** - a security feature to prevent malicious websites from stealing data.

---

## 🎯 What is CORS?

**CORS = Cross-Origin Resource Sharing**

It's a way for your backend to tell the browser: *"It's okay, I trust requests from `localhost:3000`"*

### How It Works

1. Frontend makes a request: `http://localhost:8000/chat`
2. Browser asks backend: *"Should I allow this?"*
3. Backend responds with headers:
   ```
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Methods: GET, POST
   ```
4. Browser allows the request ✅

---

## 🏗️ FastAPI's CORS Solution

FastAPI provides a **middleware** to handle CORS automatically.

### What is Middleware?

Middleware is code that runs **between** the request and your endpoint:

```
Request → Middleware → Your Endpoint → Middleware → Response
```

FastAPI's `CORSMiddleware` adds the necessary headers to every response.

---

## 📝 The Code

### Step 1: Import CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware
```

### Step 2: Add It to Your App
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Which origins can access (localhost:3000, etc.)
    allow_credentials=True,         # Allow cookies
    allow_methods=["*"],            # Which HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # Which headers are allowed
)
```

### Breaking Down the Options

| Option | What It Means | Example |
|--------|--------------|---------|
| `allow_origins` | Which domains can access your API | `["http://localhost:3000"]` or `["*"]` for all |
| `allow_credentials` | Can browser send cookies? | `True` if using auth |
| `allow_methods` | Which HTTP methods are allowed | `["GET", "POST"]` or `["*"]` for all |
| `allow_headers` | Which headers can be sent | `["*"]` is usually fine |

---

## ⚠️ Security Considerations

### Development vs Production

**Development** (what we're doing now):
```python
allow_origins=["*"]  # Allow ALL origins - convenient for testing
```

**Production** (real deployment):
```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]  # Only allow your actual frontend domain
```

**Why?** `allow_origins=["*"]` means **any website** can call your API. Fine for learning, dangerous in production!

---

## 🔄 How This Helps Our Project

Once we add CORS middleware:
1. ✅ `prototype-chat.html` can call `/chat` endpoint
2. ✅ Future dashboard can call `/ideas` endpoint
3. ✅ No more "blocked by CORS policy" errors

---

## 🛠️ What We'll Build

We'll update `main.py` to:
1. Import `CORSMiddleware`
2. Add it to the app with proper configuration
3. Test it with our frontend

Ready to make frontend and backend work together?
