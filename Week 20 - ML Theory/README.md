# Week 20: AI/ML Theory & Foundations

## 🎯 Goal
Understand the "why" behind AI systems, not just the "how."

---

## 📚 Core Concepts

### 1. Transformer Architecture

The foundation of all modern LLMs (GPT, Claude, Llama, etc.)

```
Input Tokens → Embeddings → [Attention Layers] → Output Probabilities
                                   ↓
                          Self-Attention: "Which tokens matter for this token?"
```

**Key Concepts:**

| Concept | What It Does | Interview Question |
|---------|--------------|-------------------|
| **Self-Attention** | Each token looks at all other tokens | "Explain attention mechanism" |
| **Multi-Head** | Multiple attention patterns in parallel | "Why multiple heads?" |
| **Positional Encoding** | Tells model token order | "How does order matter?" |
| **Layer Normalization** | Stabilizes training | "What helps training?" |

**Attention Formula (Simplified):**
```
Attention(Q, K, V) = softmax(QK^T / √d) × V

Q = Query (what am I looking for?)
K = Key (what do I contain?)
V = Value (what do I provide?)
```

---

### 2. LLM Internals

**How Text Generation Works:**
```
"The cat sat on the" → Model → Probability Distribution:
  - "mat": 0.35
  - "floor": 0.25
  - "bed": 0.20
  - "roof": 0.05
  - ...
```

**Key Parameters:**

| Parameter | Effect | When to Use |
|-----------|--------|-------------|
| **Temperature** | Randomness (0=deterministic, 2=creative) | 0 for facts, 0.7 for creative |
| **Top-p** | Consider top X% probability | 0.9 for balanced output |
| **Top-k** | Consider only top K tokens | 40-100 for diversity |
| **Max Tokens** | Output length limit | Set based on use case |

---

### 3. Probability & Statistics

**Must-Know Concepts:**

| Concept | Why It Matters |
|---------|----------------|
| **Bayes' Theorem** | Understanding posteriors, priors |
| **Normal Distribution** | Embeddings, model weights |
| **Cross-Entropy Loss** | How models learn |
| **Softmax** | Converting scores to probabilities |

**Bayes' Theorem:**
```
P(A|B) = P(B|A) × P(A) / P(B)

Example: Given this output, what's the probability the model is correct?
```

---

### 4. Evaluation Metrics

**For Classification:**
| Metric | When to Use |
|--------|-------------|
| **Accuracy** | Balanced classes |
| **Precision** | Minimize false positives |
| **Recall** | Minimize false negatives |
| **F1 Score** | Balance precision/recall |

**For LLMs:**
| Metric | What It Measures |
|--------|-----------------|
| **Perplexity** | How "surprised" the model is |
| **BLEU** | Token overlap (translation) |
| **ROUGE** | Summary quality |
| **Human Eval** | Actual quality (gold standard) |

---

## 📖 Study Resources

### Priority 1: Transformers
1. **Video**: [Andrej Karpathy - Let's build GPT](https://www.youtube.com/watch?v=kCc8FmEb1nY)
2. **Blog**: [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
3. **Paper**: "Attention Is All You Need" (sections 1-3)

### Priority 2: Statistics
1. **YouTube**: [StatQuest with Josh Starmer](https://www.youtube.com/@statquest)
   - Probability basics
   - Bayes' Theorem
   - Cross-entropy
2. **Practice**: Khan Academy Statistics

### Priority 3: Deep Learning
1. **Course**: [fast.ai Practical Deep Learning](https://course.fast.ai/)
2. **Book**: "Deep Learning" by Goodfellow (Chapters 1-6)

---

## 🎤 Interview Questions

### Conceptual
1. Explain how transformers work at a high level
2. What is attention and why is it important?
3. How do you evaluate an LLM for production use?
4. What's the difference between fine-tuning and prompting?
5. Explain the bias-variance tradeoff

### Practical
1. Your model has high precision but low recall - what do you do?
2. How would you detect model drift in production?
3. When would you use temperature=0 vs temperature=1?
4. How do you handle a 32K context limit with 100K documents?

---

## ✅ Weekly Checklist

- [ ] Watch Karpathy's GPT video
- [ ] Read Illustrated Transformer
- [ ] Study StatQuest: Bayes, Cross-entropy
- [ ] Practice explaining attention mechanism
- [ ] Review LLM generation parameters

---

## 🧠 Quick Reference Card

```
TRANSFORMERS
├── Self-Attention: Token relationships
├── Multi-Head: Parallel attention patterns
├── Feed-Forward: Process each position
└── Layer Norm: Training stability

LLM GENERATION
├── Temperature: 0=precise, 1=creative
├── Top-p: Probability mass cutoff
├── Top-k: Fixed token cutoff
└── Beam Search: Generate multiple paths

EVALUATION
├── Perplexity: Lower is better
├── BLEU/ROUGE: Text similarity
└── Human Eval: Ground truth
```
