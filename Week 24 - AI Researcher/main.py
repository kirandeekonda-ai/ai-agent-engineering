import asyncio
import json
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
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
    Multi-agent research pipeline using Server-Sent Events (SSE) for real-time streaming.
    """
    # Persist session to DB
    new_session = models.ResearchSession(query=query)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    async def event_generator():
        def emit(event_type: str, **kwargs):
            return f"data: {json.dumps({'type': event_type, **kwargs})}\n\n"

        yield emit("log", message="[Planner] Analyzing query and planning search strategy...")

        # ── Step 1: Query Planning ──────────────────────────────────────────────
        search_queries = await asyncio.get_event_loop().run_in_executor(
            None, query_planner_agent, query
        )
        yield emit("log", message=f"[Planner] Generated {len(search_queries)} targeted search queries.")

        # ── Step 2: Orchestration (initial strategy) ────────────────────────────
        yield emit("log", message="[Orchestrator] Determining research strategy...")
        strategy = await asyncio.get_event_loop().run_in_executor(
            None, orchestrator_agent, query, 0
        )
        min_sources   = strategy.get("min_sources", 3)
        max_iterations = strategy.get("max_iterations", 5)
        synthesis_model = strategy.get("synthesis_model", "meta-llama/llama-4-maverick-17b-128e-instruct")

        yield emit("log", message=f"[Orchestrator] Strategy set: need {min_sources} strong sources (max {max_iterations} iterations).")

        # ── Step 3: Agentic Research Loop ──────────────────────────────────────
        cache: list[dict] = []          # validated, relevant content
        all_search_results: list = []   # for source cards in the UI
        iteration = 0
        cache_lock = asyncio.Lock()     # Prevents race conditions when appending to cache

        # Helper function to process a single URL concurrently
        async def process_url(url: str, title: str, queue: asyncio.Queue):
            async with cache_lock:
                if len(cache) >= min_sources:
                    return # Stop processing if we already have enough sources
            
            try:
                await queue.put(emit("log", message=f"[Scraper] Deep reading: {title[:50]}..."))
                content = await deep_scrape(url)

                await queue.put(emit("log", message=f"[Judge] Scoring relevance of: {title[:50]}..."))
                judgment = await asyncio.get_event_loop().run_in_executor(
                    None, relevance_judge_agent, query, url, content
                )

                if judgment.get("verdict") == "KEEP":
                    score = judgment.get('score', 0)
                    await queue.put(emit("log", message=f"✅ [Judge] Kept source! Score: {score}/10"))
                    
                    async with cache_lock:
                        # Double check we didn't fill up while judging
                        if len(cache) < min_sources:
                            cache.append({
                                "url": url,
                                "title": title,
                                "content": content,
                                "score": score,
                                "reason": judgment.get("reason", ""),
                            })
                            # Persist to DB
                            db.add(models.ScrapedContent(
                                session_id=new_session.id,
                                url=url,
                                content=content,
                            ))
                else:
                    await queue.put(emit("log", message=f"❌ [Judge] Discarded source (Score {judgment.get('score', 0)})"))

            except Exception as e:
                await queue.put(emit("log", message=f"[Error] Scrape failed for {url[:30]}: {str(e)}"))


        for search_query in search_queries:
            if iteration >= max_iterations:
                break
            if len(cache) >= min_sources:
                yield emit("log", message=f"[Loop] Cache full ({len(cache)} sources), breaking early.")
                break

            iteration += 1
            yield emit("log", message=f"[Search] Iteration {iteration}/{max_iterations}: Querying '{search_query}'...")

            # 3a. Tavily search
            try:
                search_results = await search_tavily(search_query)
                all_search_results.extend(search_results)
            except Exception as e:
                yield emit("log", message=f"[Error] Search failed: {str(e)}")
                continue

            # 3b. Playwright deep-scrape + relevance judge in parallel
            urls_to_process = [r for r in search_results[:2]]
            
            # Fire off all URLs concurrently and pipe their logs to a queue
            event_queue = asyncio.Queue()
            
            # Create tasks
            tasks = [
                asyncio.create_task(process_url(r["url"], r.get("title", r["url"]), event_queue)) 
                for r in urls_to_process
            ]
            
            # Helper to wait for all tasks, so we can run it concurrently with the queue flusher
            async def run_all():
                await asyncio.gather(*tasks, return_exceptions=True)
                
            wait_task = asyncio.create_task(run_all())
            
            # While the tasks are running, flush the event queue to the SSE stream
            while not wait_task.done() or not event_queue.empty():
                try:
                    # Wait up to 0.1s for a new event
                    event_str = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield event_str
                except asyncio.TimeoutError:
                    # No new event, just loop and check if tasks are done
                    continue
            
        db.commit()
        yield emit("log", message=f"[Loop] Done — {len(cache)} high-quality sources cached.")


        # ── Step 4: Synthesis ───────────────────────────────────────────────────
        yield emit("log", message=f"[Synthesis] Writing final report using {synthesis_model}...")
        final_report = await asyncio.get_event_loop().run_in_executor(
            None, synthesis_agent, query, cache, synthesis_model
        )

        # Update session
        new_session.summary = final_report
        db.commit()

        # Build sources for the frontend (deduplicated)
        seen = set()
        sources = []
        
        # 1. Add all deeply read / cached sources FIRST so their 1-based index 
        # aligns exactly with the Source [1], Source [2] citations used by Synthesis
        for c in cache:
            url = c["url"]
            if url not in seen:
                seen.add(url)
                sources.append({
                    "url": url,
                    "title": c.get("title", url),
                    "snippet": c.get("content", "")[:150] + "...",
                    "verified": True,
                    "score": c.get("score")
                })
        
        # 2. Add remaining Tavily search results (unverified)
        for r in all_search_results:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                sources.append({
                    "url": url,
                    "title": r.get("title", url),
                    "snippet": r.get("content", "")[:150] + "...",
                    "verified": False,
                    "score": None,
                })

        yield emit("result",
            session_id=new_session.id,
            query=query,
            summary=final_report,
            sources=sources[:10], # allow up to 10 sources
            meta={
                "iterations": iteration,
                "cached_sources": len(cache),
                "synthesis_model": synthesis_model,
            }
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
