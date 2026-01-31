# AI Agent Engineering

A hands-on, production-focused tutorial for building AI agents with **LangGraph** and **LangChain**.

This course takes you from zero to Staff/Principal-level AI engineering skills through progressive, weekly modules.

---

## 🎯 What You'll Build

| Week | Project | Key Pattern |
|------|---------|-------------|
| 1 | Research Agent | Stateful graphs, tool calling |
| 2 | Router Agent | Structured output, loop prevention |
| 3 | Approval Agent | Human-in-the-loop, checkpointing |
| 4 | RAG Agent | Vector stores, embeddings |
| 5 | Research Team | Multi-agent, supervisor-worker |
| 6 | API Orchestrator | Tool composition, external APIs |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- API Keys: [Groq](https://console.groq.com), [Tavily](https://tavily.com), [LangSmith](https://smith.langchain.com)

### Setup
```bash
# Clone the repo
git clone https://github.com/kirandeekonda-ai/ai-agent-engineering.git
cd ai-agent-engineering

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install langgraph langchain langchain-groq python-dotenv tavily-python

# Configure API keys
cp .env.example .env
# Edit .env with your keys
```

### Run Any Week
```bash
# Week 1: Research Agent
python "Week 1 - Stateful Graphs/research_agent.py"

# Week 2: Router Agent
python "Week 2 - Orchestration/router_agent.py" "Your question here"

# Week 3: Approval Agent (interactive)
python "Week 3 - Persistence/approval_agent.py"

# Week 4: RAG Agent
python "Week 4 - RAG/rag_agent.py" "How many annual leave days?"

# Week 5: Multi-Agent Research Team
python "Week 5 - Multi-Agent/research_team.py"

# Week 6: API Orchestrator
python "Week 6 - APIs/api_orchestrator.py"
```

---

## 📚 Module Overview

### Module 1: Production-Grade Agentic Orchestration (Weeks 1-3)

**Week 1: Stateful Graphs**
- LangGraph fundamentals
- StateGraph and nodes
- Tool integration with Tavily

**Week 2: Router Pattern**
- Structured output with Pydantic
- Preventing infinite loops
- Central decision-making

**Week 3: Human-in-the-Loop**
- `interrupt_before` for approvals
- Checkpointing with MemorySaver
- Resume from paused state

### Module 2: Enterprise Integration (Weeks 4-6)

**Week 4: RAG & Vector Stores**
- Document chunking
- HuggingFace embeddings
- ChromaDB vector store
- Retrieval-augmented generation

**Week 5: Multi-Agent Systems**
- Supervisor-worker pattern
- Agent coordination
- Shared state management

**Week 6: External APIs**
- Tool composition
- Multiple API integration
- Weather, stock, news APIs

---

## 🏗️ Project Structure

```
ai-agent-engineering/
├── Week 1 - Stateful Graphs/
│   ├── research_agent.py     # Basic agent with tools
│   └── hello_langgraph.py    # Minimal example
├── Week 2 - Orchestration/
│   └── router_agent.py       # Structured output routing
├── Week 3 - Persistence/
│   └── approval_agent.py     # Human-in-the-loop
├── Week 4 - RAG/
│   ├── rag_agent.py          # Document Q&A
│   └── documents/            # Sample documents
├── Week 5 - Multi-Agent/
│   └── research_team.py      # Supervisor + workers
├── Week 6 - APIs/
│   └── api_orchestrator.py   # Multi-API integration
├── .env.example              # API key template
└── README.md
```

---

## 🔑 Environment Variables

Create a `.env` file with:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=AI Agent Engineering
```

---

## 📖 Learning Path

1. **Start with Week 1** - Understand basic agent structure
2. **Progress sequentially** - Each week builds on the previous
3. **Run the code** - Modify and experiment
4. **Check LangSmith** - Visualize agent execution traces

---

## 🧠 Key Concepts

| Concept | Description |
|---------|-------------|
| **StateGraph** | Directed graph for agent orchestration |
| **Structured Output** | Force LLM to return specific JSON schema |
| **Tool Binding** | Connect external APIs to LLM |
| **Checkpointing** | Save and resume graph state |
| **Multi-Agent** | Coordinate multiple specialized agents |

---

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines first.

---

## 📄 License

MIT License - feel free to use for learning and teaching.

---

## 👨‍💻 Author

**Kiran Deekonda**  
AI Engineer | [GitHub](https://github.com/kirandeekonda-ai)
