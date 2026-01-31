"""
Week 5: Multi-Agent Research Team

This demonstrates the Supervisor-Worker pattern:
- Supervisor: Routes tasks, decides which worker to call
- Researcher: Searches web for facts using Tavily
- Writer: Synthesizes facts into a report
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Literal, List
import operator
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from tavily import TavilyClient

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- TOOLS ---
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    print(f"    [Tavily] Searching: '{query}'")
    try:
        response = tavily_client.search(query=query, max_results=3)
        results = response.get("results", [])
        if results:
            return "\n".join([
                f"- {r.get('title', 'N/A')}: {r.get('content', '')[:300]}"
                for r in results[:3]
            ])
        return "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

# --- STRUCTURED OUTPUT FOR SUPERVISOR ---
class SupervisorDecision(BaseModel):
    """Supervisor's decision on which worker to assign next."""
    reasoning: str = Field(description="Why this worker/action was chosen")
    next_worker: Literal["researcher", "writer", "FINISH"] = Field(
        description="Which worker to delegate to, or FINISH if task is complete"
    )
    task_for_worker: str = Field(
        description="Specific instructions for the chosen worker"
    )

# --- MODELS ---
# Using faster 8b model for multi-agent (multiple LLM calls)
supervisor_llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
).with_structured_output(SupervisorDecision)

worker_llm = ChatGroq(
    temperature=0.3,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- STATE ---
class TeamState(TypedDict):
    user_request: str
    research_notes: str  # Accumulated research
    draft_report: str    # Writer's output
    supervisor_decision: SupervisorDecision
    iteration_count: int  # Safety limit

# --- AGENT NODES ---
def supervisor_node(state: TeamState) -> dict:
    """
    The Supervisor analyzes progress and decides next step.
    """
    print("\n[SUPERVISOR] Analyzing task...", flush=True)
    
    user_request = state["user_request"]
    research = state.get("research_notes", "")
    draft = state.get("draft_report", "")
    iterations = state.get("iteration_count", 0)
    
    # Safety: max 4 iterations
    if iterations >= 4:
        return {
            "supervisor_decision": SupervisorDecision(
                reasoning="Max iterations reached, finishing with current output",
                next_worker="FINISH",
                task_for_worker=""
            ),
            "iteration_count": iterations + 1
        }
    
    system_prompt = """You are the Supervisor of a research team.

Your team:
- researcher: Can search the web for facts and data
- writer: Can synthesize research into a coherent report

Your job:
1. Analyze the user's request
2. If research is needed and not yet done, delegate to researcher
3. If research is complete but no report exists, delegate to writer
4. If a satisfactory report exists, choose FINISH

Be efficient - don't over-research or over-write."""

    context = f"""
User Request: {user_request}

Research Notes: {research if research else "None yet"}

Draft Report: {draft if draft else "None yet"}

What should we do next?"""

    decision = supervisor_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=context)
    ])
    
    print(f"    Decision: {decision.next_worker}")
    print(f"    Reasoning: {decision.reasoning}")
    
    return {
        "supervisor_decision": decision,
        "iteration_count": iterations + 1
    }

def researcher_node(state: TeamState) -> dict:
    """
    The Researcher searches the web for facts.
    """
    task = state["supervisor_decision"].task_for_worker
    print(f"\n[RESEARCHER] Working on: {task}", flush=True)
    
    # Search using Tavily
    results = web_search.invoke({"query": task})
    
    # Accumulate research
    existing = state.get("research_notes", "")
    new_notes = f"{existing}\n\n## Research: {task}\n{results}"
    
    print(f"    Found information, adding to notes")
    return {"research_notes": new_notes.strip()}

def writer_node(state: TeamState) -> dict:
    """
    The Writer synthesizes research into a report.
    """
    task = state["supervisor_decision"].task_for_worker
    research = state.get("research_notes", "")
    print(f"\n[WRITER] Drafting: {task}", flush=True)
    
    system_prompt = """You are a professional business writer.
Write a concise, well-structured report based on the research provided.
Use bullet points and clear sections. Be factual and cite the data."""

    user_prompt = f"""
Task: {task}

Research Notes:
{research}

Write the report:"""

    response = worker_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    print(f"    Draft complete")
    return {"draft_report": response.content}

def finish_node(state: TeamState) -> dict:
    """
    Finalize and output the report.
    """
    print("\n[FINISH] Task complete")
    return {}

# --- ROUTING ---
def route_supervisor(state: TeamState) -> str:
    decision = state.get("supervisor_decision")
    if decision:
        return decision.next_worker
    return "FINISH"

# --- BUILD GRAPH ---
workflow = StateGraph(TeamState)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("finish", finish_node)

# Define edges
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "researcher": "researcher",
        "writer": "writer",
        "FINISH": "finish"
    }
)
workflow.add_edge("researcher", "supervisor")  # Report back to supervisor
workflow.add_edge("writer", "supervisor")      # Report back to supervisor
workflow.add_edge("finish", END)

app = workflow.compile()

# --- RUN ---
if __name__ == "__main__":
    import sys
    
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Write a brief report on NextPower (NXT) stock performance"
    
    print("=" * 60)
    print(f"USER REQUEST: {query}")
    print("=" * 60)
    
    result = app.invoke({
        "user_request": query,
        "research_notes": "",
        "draft_report": "",
        "supervisor_decision": None,
        "iteration_count": 0
    })
    
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print("=" * 60)
    print(result.get("draft_report", "No report generated"))
