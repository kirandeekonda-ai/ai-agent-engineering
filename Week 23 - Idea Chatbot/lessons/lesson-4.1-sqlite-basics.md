# Module 4, Lesson 4.1: SQLite Basics - Persistent Storage

## 📚 What We're Learning Today

Right now, everything is stored in RAM. Restart the server → everything disappears! SQLite will make your data **permanent**.

---

## 🤔 Why SQLite?

| Feature | In-Memory (Current) | SQLite |
|---------|-------------------|---------|
| **Persistence** | ❌ Lost on restart | ✅ Saved to disk |
| **Scalability** | ❌ Limited by RAM | ✅ Handles millions of rows |
| **Querying** | ❌ Manual loops | ✅ SQL queries |
| **Complexity** | ✅ Simple | ✅ Also simple! |

**SQLite advantages:**
- Zero configuration (no server needed)
- Built into Python
- Single file database
- Perfect for learning and small-to-medium apps

---

## 🏗️ Database Schema

We need two tables:

### 1. **ideas** - Submitted ideas
```sql
CREATE TABLE ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    problem_solved TEXT,
    time_estimate TEXT,
    cost_estimate TEXT,
    resources_needed TEXT,  -- JSON array as string
    impact TEXT,
    complexity TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'submitted'
)
```

### 2. **conversations** (Optional for Module 5)
Store full conversation history permanently.

---

## 📝 Python + SQLite

Python has built-in SQLite support:

```python
import sqlite3

# Connect to database (creates file if doesn't exist)
conn = sqlite3.connect('ideas.db')
cursor = conn.cursor()

# Execute SQL
cursor.execute("CREATE TABLE ideas (...)")

# Save (commit)
conn.commit()

# Close
conn.close()
```

---

## 🛠️ Implementation Plan

1. Create `database.py` with connection and initialization
2. Define the schema and create tables
3. Add CRUD functions (Create, Read, Update, Delete)
4. Update `/extract` endpoint to **save** ideas
5. Add `/ideas` endpoint to **retrieve** all ideas

Ready to build the database layer?
