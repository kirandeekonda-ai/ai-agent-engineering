import chromadb
import uuid
import hashlib
from langsmith import traceable

# Initialize a persistent client so memory survives restarts
# This will create a folder called ./chroma_db in the project root
client = chromadb.PersistentClient(path="./chroma_db")

# Create or get the collection for our verified internet sources
collection = client.get_or_create_collection(
    name="verified_sources",
    metadata={"hnsw:space": "cosine"} # Cosine similarity usually works best for semantic text search
)

def _generate_id(url: str) -> str:
    """Generate a consistent ID based on the URL to prevent exact duplicates"""
    return hashlib.md5(url.encode('utf-8')).hexdigest()

@traceable(name="memory_store")
def add_to_memory(url: str, title: str, content: str):
    """
    Store a validated, deep-scraped source into the vector database.
    ChromaDB will automatically embed the 'document' using its default model.
    """
    doc_id = _generate_id(url)
    
    # We only store a snippet to avoid giant embeddings, but enough to capture the meaning
    text_snippet = content[:5000] if content else ""
    
    collection.upsert(
        documents=[text_snippet],
        metadatas=[{"url": url, "title": title}],
        ids=[doc_id]
    )
    print(f"[Memory] Upserted source into vector DB: {url}")

@traceable(name="memory_search")
def search_memory(query: str, n_results: int = 2) -> list[dict]:
    """
    Query the vector database for sources relevant to the user's research topic.
    Returns a list of dicts that emulate our standard 'cache' format:
    [{ "url": ..., "title": ..., "content": ..., "score": ... }]
    """
    # Count how many items are actually in the DB to avoid errors if n_results > count
    count = collection.count()
    if count == 0:
        return []
        
    actual_results = min(n_results, count)
    
    # Query ChromaDB. It automatically turns the query string into a vector 
    # and finds the mathematically closest documents.
    results = collection.query(
        query_texts=[query],
        n_results=actual_results
    )
    
    memory_hits = []
    
    # Check if we got anything back
    if results and results['documents'] and len(results['documents'][0]) > 0:
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0] # Lower distance = higher similarity
        
        for i in range(len(docs)):
            # Distances from the default all-MiniLM model usually range from 0.0 to ~1.0. 
            # Lowering threshold from 0.6 to 0.4 so we only get strong semantic matches
            if distances[i] < 0.4:
                # Reconstruct our standard cache object
                memory_hits.append({
                    "url": metas[i]["url"],
                    "title": metas[i]["title"],
                    "content": docs[i] + "\n\n[Retrieved from persistent memory]",
                    "score": 10, # If it's in memory, it was already judged as a 10/10 KEEP!
                    "reason": "Retrieved from ChromaDB memory across sessions.",
                    "from_memory": True
                })
                
    return memory_hits
