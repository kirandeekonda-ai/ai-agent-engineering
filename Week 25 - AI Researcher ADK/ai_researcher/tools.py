"""
Tools for the ADK AI Researcher.
These are plain Python functions that ADK agents can call as tools.
ADK auto-discovers function signatures from the type hints and docstrings.
"""
import os
import re
import httpx
import hashlib
import chromadb
from dotenv import load_dotenv

load_dotenv()

# ── ChromaDB Setup ─────────────────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="verified_sources",
    metadata={"hnsw:space": "cosine"}
)


def search_web(query: str) -> dict:
    """Search the web using Tavily API for the given query. Returns a list of results with urls, titles and snippets."""
    api_key = os.getenv("TAVILY_API_KEY")
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "search_depth": "advanced", "max_results": 5},
        )
        results = response.json().get("results", [])
        return {
            "status": "success",
            "results": [
                {"url": r["url"], "title": r.get("title", ""), "snippet": r.get("content", "")[:200]}
                for r in results[:3]
            ]
        }


def scrape_page(url: str) -> dict:
    """Scrape a webpage and extract its text content using httpx."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            response = client.get(url, headers=headers)
            # Strip HTML tags to get plain text
            text = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return {"status": "success", "url": url, "content": text[:3000]}
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}


def search_memory(query: str) -> dict:
    """Search the persistent vector memory (ChromaDB) for previously verified sources relevant to the query."""
    count = collection.count()
    if count == 0:
        return {"status": "empty", "results": []}

    actual_results = min(3, count)
    results = collection.query(
        query_texts=[query],
        n_results=actual_results
    )

    hits = []
    if results and results['documents'] and len(results['documents'][0]) > 0:
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]

        for i in range(len(docs)):
            if distances[i] < 0.4:
                hits.append({
                    "url": metas[i]["url"],
                    "title": metas[i]["title"],
                    "content": docs[i][:1500],
                    "distance": round(distances[i], 3)
                })

    return {"status": "success", "results": hits}


def save_to_memory(url: str, title: str, content: str) -> dict:
    """Save a verified high-quality source to persistent vector memory for future reuse."""
    doc_id = hashlib.md5(url.encode('utf-8')).hexdigest()
    text_snippet = content[:3000] if content else ""

    collection.upsert(
        documents=[text_snippet],
        metadatas=[{"url": url, "title": title}],
        ids=[doc_id]
    )
    return {"status": "saved", "url": url}
