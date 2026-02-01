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
| 7 | LangSmith Deep Dive | Tracing, cost tracking |
| 8 | Evaluation Framework | Datasets, evaluators |
| 9 | Production Monitor | A/B testing, alerts |
| 10 | Prompt Injection Defense | Input validation, pattern detection |
| 11 | PII Protection | Data privacy, masking |
| 12 | Rate Limiter | Token budgets, guardrails |
| 13 | Memory Agent | Conversation history, caching |
| 14 | Streaming Agent | Real-time responses, progress |
| 15 | Agent Server | FastAPI, Docker deployment |
| 16 | LoRA Fine-tuning | PEFT, QLoRA, model adaptation |
| 17 | Vector DB Deep Dive | Hybrid search, chunking |
| 18 | Cloud ML Platforms | MLflow, CI/CD for ML |
| 19 | System Design | Architecture, scalability |
| 20 | ML Theory | Transformers, statistics |
| 21 | Leadership Skills | Communication, business |

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

# Week 7: LangSmith Deep Dive
python "Week 7 - LLMOps/langsmith_deep_dive.py"

# Week 8: Evaluation Framework
python "Week 8 - Evaluation/evaluation_framework.py"

# Week 9: Production Monitor
python "Week 9 - Monitoring/production_monitor.py"

# Week 10: Prompt Injection Defense
python "Week 10 - Security/prompt_injection_defense.py" test

# Week 11: PII Protection
python "Week 11 - Privacy/pii_protection.py" test

# Week 12: Rate Limiter
python "Week 12 - Guardrails/rate_limiter.py" test

# Week 13: Memory Agent (interactive)
python "Week 13 - Memory/memory_agent.py"

# Week 14: Streaming Agent
python "Week 14 - Streaming/streaming_agent.py"

# Week 15: Agent Server (starts API at localhost:8000)
python "Week 15 - Deployment/agent_server.py"

# Week 16: LoRA Fine-tuning
python "Week 16 - Fine-tuning/lora_finetuning.py"

# Week 17: Vector DB Deep Dive
python "Week 17 - VectorDB/vector_db_deep_dive.py"

# Week 18: Cloud ML Platforms
python "Week 18 - CloudML/cloud_ml_platforms.py"
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

### Module 3: LLMOps & Observability (Weeks 7-9)

**Week 7: LangSmith Deep Dive**
- Custom tracing with @traceable
- Token and cost tracking
- Latency analysis

**Week 8: Evaluation & Testing**
- Building evaluation datasets
- Custom evaluators (exact match, LLM judge)
- Category-based analysis

**Week 9: Production Monitoring**
- A/B testing prompts
- Quality scoring
- Alerts and dashboards

### Module 4: Security & Governance (Weeks 10-12)

**Week 10: Prompt Injection Defense**
- Input validation and sanitization
- Pattern-based injection detection
- Hardened system prompts

**Week 11: Data Privacy & PII**
- PII detection (email, phone, SSN, etc.)
- Masking before LLM processing
- Audit logging for compliance

**Week 12: Rate Limiting & Guardrails**
- Token budgets per user
- Request rate limiting
- Output content guardrails

### Module 5: Advanced Agent Patterns (Weeks 13-15)

**Week 13: Agent Memory & Caching**
- Conversation history management
- Session persistence across restarts
- Semantic caching for cost optimization

**Week 14: Streaming & Real-time**
- Token-by-token streaming
- Async streaming for concurrent tasks
- Progress tracking for multi-step operations

**Week 15: Deployment & Scaling**
- FastAPI REST API wrapper
- Docker containerization
- Health checks for load balancers

### Module 6: Production ML/LLM Engineering (Weeks 16-18)

**Week 16: LoRA Fine-tuning**
- Low-Rank Adaptation (LoRA) concepts
- QLoRA for memory efficiency
- PEFT library for fine-tuning

**Week 17: Vector Databases**
- ChromaDB, Pinecone, Weaviate comparison
- Hybrid search (semantic + keyword)
- Chunking strategies

**Week 18: Cloud ML Platforms**
- AWS SageMaker, Azure ML, GCP Vertex AI
- MLflow experiment tracking
- CI/CD for ML models

### Module 7: Principal Engineer Skills (Weeks 19-21)

**Week 19: System Design & Architecture**
- Distributed systems fundamentals
- AI-specific architecture patterns
- Design practice problems (RAG, recommendations)

**Week 20: AI/ML Theory & Foundations**
- Transformer architecture deep dive
- Probability and statistics essentials
- LLM evaluation metrics

**Week 21: Leadership, Communication & Business**
- Technical writing and presentations
- Mentoring and influence
- ROI analysis and AI governance

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
├── Week 7 - LLMOps/
│   └── langsmith_deep_dive.py # Tracing & cost tracking
├── Week 8 - Evaluation/
│   └── evaluation_framework.py # Datasets & evaluators
├── Week 9 - Monitoring/
│   └── production_monitor.py  # A/B testing & alerts
├── Week 10 - Security/
│   └── prompt_injection_defense.py # Input validation
├── Week 11 - Privacy/
│   └── pii_protection.py     # PII masking
├── Week 12 - Guardrails/
│   └── rate_limiter.py       # Rate limiting & output guards
├── Week 13 - Memory/
│   └── memory_agent.py       # Conversation history & caching
├── Week 14 - Streaming/
│   └── streaming_agent.py    # Real-time responses
├── Week 15 - Deployment/
│   ├── agent_server.py       # FastAPI server
│   ├── Dockerfile            # Container config
│   └── requirements.txt      # Dependencies
├── Week 16 - Fine-tuning/
│   └── lora_finetuning.py    # LoRA/PEFT concepts
├── Week 17 - VectorDB/
│   └── vector_db_deep_dive.py # DB comparison & search
├── Week 18 - CloudML/
│   └── cloud_ml_platforms.py # MLflow & CI/CD
├── Week 19 - System Design/
│   └── README.md             # Architecture study guide
├── Week 20 - ML Theory/
│   └── README.md             # Transformers & stats guide
├── Week 21 - Leadership/
│   └── README.md             # Soft skills guide
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
