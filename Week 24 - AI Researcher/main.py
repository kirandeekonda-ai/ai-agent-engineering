import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import httpx
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

import database
import models
from agents import (
    query_planner_agent,
    orchestrator_agent,
    relevance_judge_agent,
    synthesis_agent,
)
from langsmith import traceable

# Load .env from root folder (one level up)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

app = FastAPI(title="Personal AI Researcher")

# Allow Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    database.init_db()


@app.post("/research")
@traceable(name="research_workflow")
async def start_research(query: str, db: Session = Depends(database.get_db)):
    """
    Multi-agent research pipeline:
      1. Query Planner  — expands query into 3 targeted searches
      2. Orchestrator   — decides strategy (model choice, how many sources needed)
      3. Agentic Loop   — Tavily → Playwright → Relevance Judge → Cache (up to 5×)
      4. Synthesis      — final report from all cached high-quality sources
    """
    # Persist session to DB
    new_session = models.ResearchSession(query=query)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # ── Step 1: Query Planning ──────────────────────────────────────────────
    search_queries = await asyncio.get_event_loop().run_in_executor(
        None, query_planner_agent, query
    )

    # ── Step 2: Orchestration (initial strategy) ────────────────────────────
    strategy = await asyncio.get_event_loop().run_in_executor(
        None, orchestrator_agent, query, 0
    )
    min_sources   = strategy.get("min_sources", 3)
    max_iterations = strategy.get("max_iterations", 5)
    synthesis_model = strategy.get("synthesis_model", "meta-llama/llama-4-maverick-17b-128e-instruct")

    # ── Step 3: Agentic Research Loop ──────────────────────────────────────
    cache: list[dict] = []          # validated, relevant content
    all_search_results: list = []   # for source cards in the UI
    iteration = 0

    for search_query in search_queries:
        if iteration >= max_iterations:
            break
        if len(cache) >= min_sources:
            print(f"[loop] cache full ({len(cache)} sources), stopping early")
            break

        iteration += 1
        print(f"\n[loop] iteration {iteration}/{max_iterations}: '{search_query}'")

        # 3a. Tavily search
        try:
            search_results = await search_tavily(search_query)
            all_search_results.extend(search_results)
        except Exception as e:
            print(f"[tavily] error: {e}")
            continue

        # 3b. Playwright deep-scrape + relevance judge for top 2 URLs
        urls = [r["url"] for r in search_results[:2]]
        for url in urls:
            if len(cache) >= min_sources:
                break
            try:
                content = await deep_scrape(url)

                # 3c. Relevance judgement
                title = next((r["title"] for r in search_results if r["url"] == url), url)
                judgment = await asyncio.get_event_loop().run_in_executor(
                    None, relevance_judge_agent, query, url, content
                )

                if judgment.get("verdict") == "KEEP":
                    cache.append({
                        "url": url,
                        "title": title,
                        "content": content,
                        "score": judgment.get("score", 0),
                        "reason": judgment.get("reason", ""),
                    })
                    # Persist to DB
                    db.add(models.ScrapedContent(
                        session_id=new_session.id,
                        url=url,
                        content=content,
                    ))

            except Exception as e:
                print(f"[scrape error] {url}: {e}")
                continue

    db.commit()
    print(f"\n[loop] done — {len(cache)} sources cached across {iteration} iterations")

    # ── Step 4: Synthesis ───────────────────────────────────────────────────
    final_report = await asyncio.get_event_loop().run_in_executor(
        None, synthesis_agent, query, cache, synthesis_model
    )

    # Update session
    new_session.summary = final_report
    db.commit()

    # Build sources for the frontend (deduplicated)
    seen = set()
    sources = []
    for r in all_search_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            cached_item = next((c for c in cache if c["url"] == url), None)
            sources.append({
                "url": url,
                "title": r.get("title", url),
                "snippet": r.get("content", "")[:150] + "...",
                "verified": cached_item is not None,  # highlight deep-scraped sources
                "score": cached_item["score"] if cached_item else None,
            })

    return {
        "session_id": new_session.id,
        "query": query,
        "summary": final_report,
        "sources": sources[:8],
        "meta": {
            "iterations": iteration,
            "cached_sources": len(cache),
            "synthesis_model": synthesis_model,
        }
    }


# ── Tavily Search ──────────────────────────────────────────────────────────────

@traceable(name="tavily_search")
async def search_tavily(query: str):
    api_key = os.getenv("TAVILY_API_KEY")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "search_depth": "advanced", "days": 7},
        )
        return response.json().get("results", [])


# ── Playwright Deep Scraper ────────────────────────────────────────────────────

def _sync_scrape(url: str) -> str:
    """Runs Playwright synchronously (called from a thread executor)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        content = page.evaluate("() => document.body.innerText")
        browser.close()
        return content


@traceable(name="playwright_scrape")
async def deep_scrape(url: str):
    """Runs sync Playwright in a thread so it doesn't block the async loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_scrape, url)
