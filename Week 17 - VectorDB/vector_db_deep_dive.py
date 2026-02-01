"""
Week 17: Vector Databases Deep Dive

This script demonstrates:
1. Vector DB concepts and comparison
2. Embedding strategies and chunking
3. Semantic vs Hybrid search
4. Production RAG patterns
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- VECTOR DB COMPARISON ---
VECTOR_DBS = {
    "ChromaDB": {
        "type": "Local/Embedded",
        "hosting": "Self-hosted",
        "best_for": "Development, small projects",
        "max_vectors": "~1M",
        "features": ["Easy setup", "Python native", "No server needed"]
    },
    "Pinecone": {
        "type": "Managed Cloud",
        "hosting": "Fully managed",
        "best_for": "Production, scale",
        "max_vectors": "Billions",
        "features": ["Serverless", "Auto-scaling", "Hybrid search"]
    },
    "Weaviate": {
        "type": "Self-hosted/Cloud",
        "hosting": "Both options",
        "best_for": "Enterprise, GraphQL",
        "max_vectors": "Billions",
        "features": ["Hybrid search", "Multi-modal", "GraphQL API"]
    },
    "Qdrant": {
        "type": "Self-hosted/Cloud",
        "hosting": "Both options",
        "best_for": "High performance",
        "max_vectors": "Billions",
        "features": ["Fast", "Filtering", "Payload support"]
    }
}

# --- SIMULATED EMBEDDING MODEL ---
class SimpleEmbedder:
    """Simulates embedding generation (production: use OpenAI/Cohere)."""
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        np.random.seed(42)
    
    def embed(self, text: str) -> list[float]:
        """Generate consistent pseudo-embedding based on text."""
        # Seed based on text for consistency
        seed = sum(ord(c) for c in text) % 10000
        np.random.seed(seed)
        return np.random.rand(self.dim).tolist()
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        return [self.embed(t) for t in texts]

# --- SIMPLE VECTOR STORE (In-Memory) ---
@dataclass
class Document:
    id: str
    text: str
    embedding: list[float]
    metadata: dict

class SimpleVectorStore:
    """Simple in-memory vector store for demonstration."""
    
    def __init__(self):
        self.documents: list[Document] = []
        self.embedder = SimpleEmbedder()
    
    def add(self, text: str, metadata: dict = None) -> str:
        """Add document to store."""
        doc_id = f"doc_{len(self.documents)}"
        embedding = self.embedder.embed(text)
        
        doc = Document(
            id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {}
        )
        self.documents.append(doc)
        return doc_id
    
    def _cosine_similarity(self, a: list, b: list) -> float:
        """Calculate cosine similarity."""
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def search(self, query: str, top_k: int = 3) -> list[tuple]:
        """Semantic search."""
        query_embedding = self.embedder.embed(query)
        
        scores = []
        for doc in self.documents:
            sim = self._cosine_similarity(query_embedding, doc.embedding)
            scores.append((doc, sim))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def hybrid_search(self, query: str, top_k: int = 3) -> list[tuple]:
        """Hybrid search: semantic + keyword."""
        # Semantic scores
        semantic_results = {doc.id: sim for doc, sim in self.search(query, top_k=len(self.documents))}
        
        # Keyword scores (simple BM25-like)
        query_terms = query.lower().split()
        keyword_scores = {}
        for doc in self.documents:
            doc_terms = doc.text.lower().split()
            matches = sum(1 for t in query_terms if t in doc_terms)
            keyword_scores[doc.id] = matches / max(len(query_terms), 1)
        
        # Combine (weighted)
        combined = []
        for doc in self.documents:
            sem_score = semantic_results.get(doc.id, 0)
            kw_score = keyword_scores.get(doc.id, 0)
            final_score = 0.7 * sem_score + 0.3 * kw_score  # 70% semantic, 30% keyword
            combined.append((doc, final_score))
        
        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:top_k]

# --- CHUNKING STRATEGIES ---
def chunk_fixed(text: str, chunk_size: int = 200, overlap: int = 50) -> list[str]:
    """Fixed-size chunking with overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks

def chunk_sentence(text: str, max_sentences: int = 3) -> list[str]:
    """Sentence-based chunking."""
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = '. '.join(sentences[i:i + max_sentences]) + '.'
        chunks.append(chunk)
    return chunks

# --- SAMPLE DOCUMENTS ---
DOCUMENTS = [
    "Python is a high-level programming language known for its readability and simplicity.",
    "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
    "Vector databases store embeddings for fast similarity search and retrieval.",
    "RAG combines retrieval with generation to ground LLM responses in factual data.",
    "LangChain is a framework for building applications with large language models.",
    "Fine-tuning adapts pre-trained models to specific tasks using domain data.",
]

# --- MAIN ---
def demo_vector_db_comparison():
    """Show vector DB comparison."""
    print("=" * 60)
    print("VECTOR DATABASE COMPARISON")
    print("=" * 60)
    
    for name, info in VECTOR_DBS.items():
        print(f"\n📦 {name}")
        print(f"   Type: {info['type']}")
        print(f"   Hosting: {info['hosting']}")
        print(f"   Best for: {info['best_for']}")
        print(f"   Scale: {info['max_vectors']} vectors")
        print(f"   Features: {', '.join(info['features'])}")

def demo_search():
    """Demo semantic and hybrid search."""
    print("\n" + "=" * 60)
    print("VECTOR STORE DEMO")
    print("=" * 60)
    
    store = SimpleVectorStore()
    
    # Add documents
    print("\n📄 Adding documents...")
    for doc in DOCUMENTS:
        doc_id = store.add(doc)
        print(f"   Added: {doc_id} - {doc[:40]}...")
    
    # Semantic search
    query = "How do I build AI applications?"
    print(f"\n🔍 Query: '{query}'")
    
    print("\n--- Semantic Search ---")
    results = store.search(query, top_k=3)
    for doc, score in results:
        print(f"   [{score:.3f}] {doc.text[:50]}...")
    
    print("\n--- Hybrid Search (70% semantic + 30% keyword) ---")
    results = store.hybrid_search(query, top_k=3)
    for doc, score in results:
        print(f"   [{score:.3f}] {doc.text[:50]}...")

def demo_chunking():
    """Demo chunking strategies."""
    print("\n" + "=" * 60)
    print("CHUNKING STRATEGIES")
    print("=" * 60)
    
    text = "Python is widely used in data science. It has excellent libraries. NumPy and Pandas are popular. Machine learning frameworks like TensorFlow exist. Deep learning is also supported."
    
    print(f"\n📝 Original ({len(text)} chars):")
    print(f"   {text}")
    
    print("\n--- Fixed-size chunks (100 chars, 20 overlap) ---")
    for i, chunk in enumerate(chunk_fixed(text, 100, 20)):
        print(f"   Chunk {i+1}: {chunk[:50]}...")
    
    print("\n--- Sentence-based (2 sentences per chunk) ---")
    for i, chunk in enumerate(chunk_sentence(text, 2)):
        print(f"   Chunk {i+1}: {chunk[:50]}...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "compare":
            demo_vector_db_comparison()
        elif mode == "chunk":
            demo_chunking()
        else:
            demo_search()
    else:
        demo_vector_db_comparison()
        demo_search()
        demo_chunking()
        
        print("\n" + "=" * 60)
        print("KEY TAKEAWAYS")
        print("=" * 60)
        print("""
1. ChromaDB: Great for development and small projects
2. Pinecone: Best for production at scale
3. Hybrid search: Combines semantic + keyword for better results
4. Chunking matters: Overlap prevents context loss
5. Choose based on: scale, cost, hosting preference
        """)
