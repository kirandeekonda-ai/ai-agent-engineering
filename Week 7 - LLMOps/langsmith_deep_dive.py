"""
Week 7: LangSmith Deep Dive

This script demonstrates production LLMOps practices:
1. Custom trace metadata (tags, user IDs)
2. Token/cost tracking
3. Latency measurement
4. Annotations for analysis
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import time
from typing import TypedDict, Annotated
import operator

from langsmith import traceable, Client
from langsmith.run_helpers import get_current_run_tree
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.callbacks import BaseCallbackHandler

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Ensure tracing is enabled
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# --- LANGSMITH CLIENT ---
ls_client = Client()

# --- CUSTOM CALLBACK FOR TOKEN TRACKING ---
class TokenTracker(BaseCallbackHandler):
    """Track tokens and cost per LLM call."""
    
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
    
    def on_llm_end(self, response, **kwargs):
        """Called after each LLM response."""
        self.calls += 1
        
        # Extract token usage from response
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            self.prompt_tokens += usage.get('prompt_tokens', 0)
            self.completion_tokens += usage.get('completion_tokens', 0)
            self.total_tokens += usage.get('total_tokens', 0)
    
    def get_cost_estimate(self, model: str = "llama-3.1-8b-instant") -> float:
        """Estimate cost (Groq is free, but this shows the pattern)."""
        # Example pricing (adjust for actual provider)
        prices = {
            "llama-3.1-8b-instant": {"input": 0.0001, "output": 0.0002},
            "llama-3.3-70b-versatile": {"input": 0.0008, "output": 0.0016},
        }
        price = prices.get(model, {"input": 0.001, "output": 0.002})
        return (self.prompt_tokens * price["input"] + 
                self.completion_tokens * price["output"]) / 1000

# --- TRACEABLE FUNCTION (LangSmith decorator) ---
@traceable(
    name="process_query",
    tags=["week7", "demo"],
    metadata={"version": "1.0"}
)
def process_query(query: str, user_id: str = "demo_user") -> dict:
    """
    Process a query with full LangSmith tracing.
    The @traceable decorator automatically creates a trace.
    """
    start_time = time.time()
    
    # Create token tracker
    tracker = TokenTracker()
    
    # Model with callback
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.1-8b-instant",
        api_key=os.environ.get("GROQ_API_KEY"),
        callbacks=[tracker]
    )
    
    # Add custom metadata to current run
    run_tree = get_current_run_tree()
    if run_tree:
        run_tree.extra["metadata"] = {
            "user_id": user_id,
            "query_length": len(query),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Execute LLM call
    response = llm.invoke([
        SystemMessage(content="You are a helpful assistant. Be concise."),
        HumanMessage(content=query)
    ])
    
    # Calculate metrics
    latency = time.time() - start_time
    
    result = {
        "answer": response.content,
        "metrics": {
            "latency_seconds": round(latency, 3),
            "total_tokens": tracker.total_tokens,
            "prompt_tokens": tracker.prompt_tokens,
            "completion_tokens": tracker.completion_tokens,
            "estimated_cost": round(tracker.get_cost_estimate(), 6),
            "llm_calls": tracker.calls
        }
    }
    
    return result

# --- BATCH ANALYSIS ---
def run_batch_analysis(queries: list[str]) -> dict:
    """Run multiple queries and aggregate metrics."""
    print("\n" + "=" * 60)
    print("BATCH ANALYSIS - LangSmith Tracing Demo")
    print("=" * 60)
    
    all_metrics = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Processing: {query[:50]}...")
        
        result = process_query(query, user_id=f"user_{i}")
        all_metrics.append(result["metrics"])
        
        print(f"    Answer: {result['answer'][:100]}...")
        print(f"    Latency: {result['metrics']['latency_seconds']}s")
        print(f"    Tokens: {result['metrics']['total_tokens']}")
    
    # Aggregate stats
    total_tokens = sum(m["total_tokens"] for m in all_metrics)
    total_cost = sum(m["estimated_cost"] for m in all_metrics)
    avg_latency = sum(m["latency_seconds"] for m in all_metrics) / len(all_metrics)
    
    summary = {
        "total_queries": len(queries),
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "avg_latency": round(avg_latency, 3)
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Queries: {summary['total_queries']}")
    print(f"Total Tokens:  {summary['total_tokens']}")
    print(f"Total Cost:    ${summary['total_cost']:.6f}")
    print(f"Avg Latency:   {summary['avg_latency']}s")
    
    return summary

# --- VIEW RECENT RUNS IN LANGSMITH ---
def view_recent_runs(project_name: str = None, limit: int = 5):
    """View recent runs from LangSmith."""
    print("\n" + "=" * 60)
    print("RECENT LANGSMITH RUNS")
    print("=" * 60)
    
    try:
        runs = list(ls_client.list_runs(
            project_name=project_name or os.environ.get("LANGCHAIN_PROJECT"),
            limit=limit
        ))
        
        for run in runs:
            print(f"\nRun: {run.name}")
            print(f"  ID: {run.id}")
            print(f"  Status: {run.status}")
            print(f"  Start: {run.start_time}")
            if run.total_tokens:
                print(f"  Tokens: {run.total_tokens}")
    except Exception as e:
        print(f"Error fetching runs: {e}")
        print("Make sure LANGCHAIN_API_KEY is set correctly")

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Run batch analysis
        test_queries = [
            "What is the capital of France?",
            "Explain quantum computing in one sentence.",
            "What is 2 + 2?",
            "Name three programming languages.",
            "What is machine learning?"
        ]
        run_batch_analysis(test_queries)
    elif len(sys.argv) > 1 and sys.argv[1] == "runs":
        # View recent runs
        view_recent_runs()
    else:
        # Single query
        query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is LangSmith used for?"
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        result = process_query(query)
        
        print(f"\nAnswer: {result['answer']}")
        print(f"\nMetrics:")
        for key, value in result['metrics'].items():
            print(f"  {key}: {value}")
        
        print("\n[Check LangSmith dashboard for trace details]")
        print("https://smith.langchain.com")
