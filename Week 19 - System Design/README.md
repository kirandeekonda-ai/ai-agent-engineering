# Week 19: System Design & Architecture

## 🎯 Goal
Learn to design scalable AI systems like a Principal Engineer.

---

## 📚 Core Concepts

### 1. Distributed Systems Fundamentals

| Concept | Definition | AI Example |
|---------|------------|------------|
| **CAP Theorem** | Can only have 2 of: Consistency, Availability, Partition tolerance | Choose CP for model serving, AP for logging |
| **Sharding** | Split data across machines | Vector DB partitioning |
| **Replication** | Copy data for reliability | Model replica failover |
| **Load Balancing** | Distribute traffic | Route to multiple inference servers |

### 2. Scalability Patterns

```
Vertical Scaling: Bigger machine (limited)
Horizontal Scaling: More machines (preferred for AI)

Example: 1000 requests/sec
- 1 GPU server → bottleneck
- 10 GPU servers behind load balancer → scalable
```

### 3. AI-Specific Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI System Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ API     │───▶│ Queue   │───▶│ Inference│───▶│ Cache   │  │
│  │ Gateway │    │ (Kafka) │    │ Workers  │    │ (Redis) │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │                              │                       │
│       ▼                              ▼                       │
│  ┌─────────┐                   ┌─────────┐                  │
│  │ Rate    │                   │ Model   │                  │
│  │ Limiter │                   │ Registry│                  │
│  └─────────┘                   └─────────┘                  │
│                                      │                       │
│                                      ▼                       │
│                               ┌─────────┐                   │
│                               │ Feature │                   │
│                               │ Store   │                   │
│                               └─────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Design Practice Problems

### Problem 1: Design a RAG System (Multi-tenant)

**Requirements:**
- Support 100 companies, each with private docs
- 1M documents total
- 50 QPS across all tenants
- Sub-second latency

**Key Decisions:**
| Component | Choice | Reasoning |
|-----------|--------|-----------|
| Vector DB | Pinecone (namespaces) | Tenant isolation |
| Embedding | Cached + async | Reduce latency |
| LLM | Groq/Together | Fast inference |
| Architecture | Serverless | Scale per tenant |

---

### Problem 2: Design a Real-time Recommendation System

**Requirements:**
- 10M users
- 1M items
- 100ms latency requirement
- Update recommendations based on recent behavior

**Architecture:**
```
User Request → Feature Store Lookup → Model Inference → Cache → Response
                    ↑                       ↑
              Real-time features      Pre-computed embeddings
```

---

### Problem 3: Design a Multi-Agent Orchestration Platform

**Requirements:**
- Support 50 concurrent agent sessions
- Different agent types (RAG, Code, Research)
- Human-in-the-loop approval
- Audit logging

**Key Components:**
1. Agent Registry - Available agent types
2. Session Manager - State persistence
3. Message Queue - Agent communication
4. Checkpoint Store - Resume capability

---

## 📖 Study Resources

### Books (Priority Order)
1. **"Designing Data-Intensive Applications"** - Martin Kleppmann
   - Chapters 1-3: Foundations
   - Chapter 5: Replication
   - Chapter 6: Partitioning

2. **"System Design Interview Vol 1 & 2"** - Alex Xu
   - Focus: AI/ML specific chapters

### Online Courses
| Course | Platform | Focus |
|--------|----------|-------|
| Grokking System Design | Design Gurus | Interview prep |
| AWS ML Specialty | AWS | Cloud patterns |

### YouTube Channels
- System Design Interview (SDI)
- ByteByteGo
- Hussein Nasser

---

## ✅ Weekly Checklist

- [ ] Read DDIA Chapter 1-3
- [ ] Design RAG system on paper
- [ ] Watch 3 system design videos
- [ ] Practice whiteboard explanation
- [ ] Review cloud architecture patterns

---

## 🎤 Interview Tips

1. **Clarify Requirements First**
   - Scale (users, requests/sec)
   - Latency requirements
   - Consistency needs

2. **Start High-Level**
   - Draw boxes and arrows
   - Explain data flow

3. **Deep Dive on AI Components**
   - Model serving strategy
   - Feature engineering
   - Monitoring/observability

4. **Discuss Trade-offs**
   - Cost vs latency
   - Complexity vs maintainability
