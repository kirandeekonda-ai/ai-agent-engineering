"""
agents.py — The 4 specialist agents for the AI Researcher pipeline.

Each agent is a focused LLM call with a dedicated model and role:
  1. query_planner_agent     → llama-3.1-8b-instant  (fast, cheap)
  2. orchestrator_agent      → groq/compound-mini    (routing decisions)
  3. relevance_judge_agent   → llama-3.3-70b-versatile (nuanced reasoning)
  4. synthesis_agent         → llama-4-maverick-17b-128e-instruct (128K ctx)
"""

import json
from langsmith import traceable
from llm import call_model


# ─── Model IDs ────────────────────────────────────────────────────────────────

MODEL_PLANNER    = "llama-3.1-8b-instant"
MODEL_ORCHESTRATOR = "groq/compound-mini"
MODEL_JUDGE      = "llama-3.3-70b-versatile"
MODEL_SYNTHESIS  = "meta-llama/llama-4-maverick-17b-128e-instruct"


# ─── Agent 1: Query Planner ───────────────────────────────────────────────────

@traceable(name="agent_query_planner")
def query_planner_agent(raw_query: str) -> list[str]:
    """
    Expands a raw user query into 3 targeted, specific search strings.
    Uses a fast small model — this is a cheap preprocessing step.

    Returns: list of 3 search query strings
    """
    system = (
        "You are a search query specialist. Your job is to take a user's raw "
        "research topic and produce exactly 3 highly specific, targeted search "
        "queries that will surface the most relevant and up-to-date information. "
        "Focus on specificity: include year, product names, technical terms. "
        "Return ONLY a valid JSON array of 3 strings. No explanation, no markdown."
    )
    user = f'Expand this research topic into 3 targeted search queries: "{raw_query}"'

    raw = call_model(MODEL_PLANNER, system, user, temperature=0.4)

    # Parse — model returns JSON array
    try:
        # Strip any accidental markdown fences
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        queries = json.loads(cleaned)
        if isinstance(queries, list) and len(queries) >= 1:
            print(f"[planner] generated {len(queries)} queries: {queries}")
            return queries[:3]
    except Exception as e:
        print(f"[planner] JSON parse failed ({e}), falling back to raw query")

    # Fallback: use the original query
    return [raw_query]


# ─── Agent 2: Orchestrator ─────────────────────────────────────────────────────

@traceable(name="agent_orchestrator")
def orchestrator_agent(query: str, cache_size: int) -> dict:
    """
    Makes high-level routing decisions for the research session.
    Decides which synthesis model to use and the minimum acceptable cache size.

    Returns:
        {
          "synthesis_model": "<model_id>",
          "min_sources": <int>,    # stop early when cache reaches this size
          "max_iterations": <int>  # hard cap on search loops
        }
    """
    system = (
        "You are a research orchestrator. Given a query and how many validated "
        "sources have been found so far, decide the research strategy. "
        "Return ONLY a valid JSON object with these exact keys:\n"
        "  synthesis_model: one of 'meta-llama/llama-4-maverick-17b-128e-instruct' or 'llama-3.3-70b-versatile'\n"
        "  min_sources: integer between 2 and 5\n"
        "  max_iterations: integer between 2 and 5\n"
        "Use the maverick model for complex, broad topics. Use 70b for narrow/simple topics. "
        "No explanation, no markdown fences."
    )
    user = (
        f'Query: "{query}"\n'
        f'Validated sources found so far: {cache_size}\n'
        f'Decide the research strategy.'
    )

    raw = call_model(MODEL_ORCHESTRATOR, system, user, temperature=0.1)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        config = json.loads(cleaned)
        print(f"[orchestrator] strategy: {config}")
        return config
    except Exception as e:
        print(f"[orchestrator] JSON parse failed ({e}), using defaults")
        # Safe defaults
        return {
            "synthesis_model": MODEL_SYNTHESIS,
            "min_sources": 3,
            "max_iterations": 5,
        }


# ─── Agent 3: Relevance Judge ─────────────────────────────────────────────────

@traceable(name="agent_relevance_judge")
def relevance_judge_agent(query: str, url: str, content: str) -> dict:
    """
    Evaluates whether a scraped page is relevant and useful for the query.
    Uses a medium-strength model for nuanced reasoning.

    Returns:
        {
          "verdict": "KEEP" | "DISCARD",
          "score": 0-10,
          "reason": "<short explanation>"
        }
    """
    # Truncate content to avoid token overflow — first 3000 chars is enough to judge
    preview = content[:3000] if content else ""

    system = (
        "You are a research quality judge. You receive a user's research query "
        "and a snippet of content scraped from a webpage. "
        "Score the content's relevance from 0 to 10 and decide whether to KEEP or DISCARD it. "
        "KEEP if score >= 6. DISCARD if score < 6. "
        "Return ONLY a valid JSON object with keys: verdict, score, reason. "
        "No markdown fences, no extra text."
    )
    user = (
        f'Research query: "{query}"\n'
        f'Source URL: {url}\n\n'
        f'Content preview:\n{preview}'
    )

    raw = call_model(MODEL_JUDGE, system, user, temperature=0.1)

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
        verdict = result.get("verdict", "DISCARD")
        score   = result.get("score", 0)
        reason  = result.get("reason", "")
        print(f"[judge] {url[:60]}... → {verdict} (score: {score}) — {reason[:80]}")
        return result
    except Exception as e:
        print(f"[judge] JSON parse failed ({e}), defaulting to DISCARD")
        return {"verdict": "DISCARD", "score": 0, "reason": "parse error"}


# ─── Agent 4: Synthesis ───────────────────────────────────────────────────────

@traceable(name="agent_synthesis")
def synthesis_agent(query: str, cache: list[dict], synthesis_model: str) -> str:
    """
    Produces the final research report from all validated, cached content.
    Uses a large-context model to handle potentially 5 full page scrapes.

    Args:
        query:           The original user query
        cache:           List of dicts: [{url, title, content, score}]
        synthesis_model: Model ID chosen by the orchestrator

    Returns: Final markdown report string
    """
    if not cache:
        return "No relevant sources were found for this query. Please try a more specific search."

    # Build context from all cached items
    context_parts = []
    for i, item in enumerate(cache, 1):
        context_parts.append(
            f"### Source {i}: {item.get('title', item['url'])}\n"
            f"URL: {item['url']}\n"
            f"Relevance Score: {item.get('score', 'N/A')}/10\n\n"
            f"{item['content'][:4000]}\n"  # 4K chars per source
        )
    context = "\n---\n".join(context_parts)

    system = (
        "You are an elite AI research analyst. You synthesize information from "
        "multiple verified sources into a comprehensive, well-structured report. "
        "Use markdown formatting: ## for sections, **bold** for key terms, "
        "numbered lists for findings, bullet points for details. "
        "Always cite your sources by name or URL. Be specific — include dates, "
        "numbers, and technical details from the sources. No hallucination."
    )
    user = (
        f'Produce a comprehensive research report for the query: "{query}"\n\n'
        f'You have {len(cache)} verified, high-quality sources:\n\n'
        f'{context}'
    )

    print(f"[synthesis] using {synthesis_model} with {len(cache)} cached sources")
    return call_model(synthesis_model, system, user, temperature=0.3)
