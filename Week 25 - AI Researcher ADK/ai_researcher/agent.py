"""
AI Researcher Agent — Powered by Google ADK
This is the same 4-agent pipeline from Week 24, but defined declaratively using ADK.

Using Gemini (Google's native model) because:
- ADK has first-class Gemini support (no LiteLLM wrapper needed)
- Gemini has proper tool-calling that works flawlessly with ADK
- Free tier: 15 RPM, 1M TPM — far more generous than Groq's free tier
"""
from datetime import datetime
from google.adk.agents import LlmAgent, SequentialAgent
from .tools import search_web, scrape_page, search_memory, save_to_memory


today = datetime.now().strftime("%B %d, %Y")

# ── Agent 1: Query Planner ─────────────────────────────────────────────────────
query_planner = LlmAgent(
    name="QueryPlanner",
    model="gemini-2.0-flash",
    instruction=f"""You are a search query specialist. Today's date is {today}.
Your job is to take a user's raw research topic and produce exactly 3 highly specific,
targeted search queries that will surface the most relevant and up-to-date information.
If the user asks for 'latest' or 'recent', always include the current year or month.
Focus on specificity: include product names, technical terms.
Return ONLY a valid JSON array of 3 strings. No explanation, no markdown.""",
    description="Expands the user's research topic into 3 targeted search queries.",
    output_key="search_queries"
)

# ── Agent 2: Research Worker ───────────────────────────────────────────────────
researcher = LlmAgent(
    name="Researcher",
    model="gemini-2.0-flash",
    instruction=f"""You are an expert research agent. Today's date is {today}.

You have tools: search_web, scrape_page, search_memory, save_to_memory.

IMPORTANT: Be very efficient. Make as FEW tool calls as possible:
1. Call search_web ONCE with the user's query.
2. Call scrape_page on the top 1-2 results only.
3. Call save_to_memory for any good source found.
4. Return a summary of the sources you found with their URLs, titles and key content.

Do NOT make more than 5 total tool calls.""",
    description="Searches, scrapes, judges, and caches research sources.",
    tools=[search_web, scrape_page, search_memory, save_to_memory],
    output_key="research_results"
)

# ── Agent 3: Synthesis ─────────────────────────────────────────────────────────
synthesizer = LlmAgent(
    name="Synthesizer",
    model="gemini-2.0-flash",
    instruction=f"""You are an elite AI research analyst. Today's date is {today}.
You synthesize information from multiple verified sources into a comprehensive,
well-structured research report.

Use markdown formatting: ## for sections, **bold** for key terms, numbered lists
for findings, bullet points for details.

**CRITICAL CITATION RULES:**
1. You MUST cite your sources using strict numerical brackets at the end of EVERY factual claim.
2. The citations MUST be clickable markdown links formatted exactly like this: [[1]](URL)
3. Never hallucinate facts. Only state what is explicitly in the sources.

Read the research results from the previous agent and produce the report.
At the end, include a "## Sources" section listing all cited URLs.""",
    description="Writes a comprehensive research report with inline citations.",
    output_key="final_report"
)

# ── Root Agent: Sequential Pipeline ────────────────────────────────────────────
root_agent = SequentialAgent(
    name="AIResearcher",
    sub_agents=[query_planner, researcher, synthesizer],
    description="A multi-agent AI research pipeline that searches, validates, and synthesizes information."
)
