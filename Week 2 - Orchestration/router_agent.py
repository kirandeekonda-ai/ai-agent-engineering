"""
Week 2: Router Agent with Structured Output

This agent uses a CENTRAL ROUTER to control the flow.
The Router decides: "Search" or "Finish" - no more infinite loops.
"""
from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Literal, Optional
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

# 1. SETUP ENV
load_dotenv()

# --- REAL TAVILY SEARCH ---
from tavily import TavilyClient

tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the internet for current information using Tavily."""
    print(f"\n[TOOL] Searching Tavily for '{query}'")
    try:
        response = tavily_client.search(query=query, max_results=3)
        results = response.get("results", [])
        if results:
            # Combine top results into a coherent answer
            combined = "\n".join([
                f"- {r.get('title', 'No title')}: {r.get('content', 'No content')[:200]}"
                for r in results[:3]
            ])
            return combined
        return "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

tools = [web_search]

# 2. STRUCTURED OUTPUT SCHEMA (THE KEY TO STOPPING LOOPS)
class RouterDecision(BaseModel):
    """The Router's decision on what to do next."""
    reasoning: str = Field(description="Brief explanation of why this action was chosen")
    action: Literal["search", "answer"] = Field(
        description="'search' if more information is needed, 'answer' if we can respond now"
    )
    search_query: Optional[str] = Field(
        default=None, 
        description="If action is 'search', what to search for"
    )
    final_answer: Optional[str] = Field(
        default=None,
        description="If action is 'answer', the complete response to the user"
    )

# 3. DEFINE MODELS
# Router Model: Uses Structured Output (JSON mode)
# Using 70b model for more reliable structured output
router_llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY")
).with_structured_output(RouterDecision)

# Worker Model: For tool calling
worker_llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY")
).bind_tools(tools)

# 4. DEFINE STATE
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    search_results: str  # Accumulated search results
    router_decision: Optional[RouterDecision]  # Last router decision

# 5. DEFINE NODES

def router_node(state: AgentState) -> dict:
    """
    THE CENTRAL ROUTER (The Brain)
    Decides: Do we need to search, or can we answer?
    """
    print("\n[ROUTER] Analyzing...")
    
    messages = state["messages"]
    search_results = state.get("search_results", "")
    
    # Build context for the router
    system_prompt = """You are a routing agent. Analyze the user's question and any search results.

Rules:
1. If you have enough information to answer the question completely, choose 'answer'.
2. If you need more information, choose 'search' and provide a specific query.
3. NEVER search more than once for the same type of information.
4. If search results already contain the answer, you MUST choose 'answer'."""

    user_context = f"""
User Question: {messages[0].content}

Search Results So Far:
{search_results if search_results else "None yet"}

What should we do next?"""

    decision = router_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_context)
    ])
    
    print(f"   Decision: {decision.action}")
    print(f"   Reasoning: {decision.reasoning}")
    
    return {"router_decision": decision}

def search_node(state: AgentState) -> dict:
    """
    THE WORKER: Executes the search.
    Does NOT decide anything - just fetches data.
    """
    decision = state["router_decision"]
    query = decision.search_query or "general information"
    
    # Call the mock tool directly
    result = web_search.invoke({"query": query})
    
    # Accumulate results
    existing = state.get("search_results", "")
    new_results = f"{existing}\n- {result}" if existing else f"- {result}"
    
    return {"search_results": new_results}

def answer_node(state: AgentState) -> dict:
    """
    THE FINALIZER: Delivers the final answer.
    """
    decision = state["router_decision"]
    print(f"\n[ANSWER] {decision.final_answer}")
    
    return {"messages": [AIMessage(content=decision.final_answer)]}

# 6. CONDITIONAL LOGIC
def route_decision(state: AgentState) -> str:
    """Route based on the router's decision."""
    decision = state.get("router_decision")
    if decision and decision.action == "search":
        return "search"
    return "answer"

# 7. BUILD GRAPH
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("search", search_node)
workflow.add_node("answer", answer_node)

# Define edges
workflow.set_entry_point("router")
workflow.add_conditional_edges("router", route_decision, {"search": "search", "answer": "answer"})
workflow.add_edge("search", "router")  # After search, go back to router to decide again
workflow.add_edge("answer", END)  # Answer ends the graph

app = workflow.compile()

# 8. RUN
if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "What is the stock price of NVIDIA?"
    print(f"Goal: {query}")
    print("=" * 50)
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "search_results": "",
        "router_decision": None
    }
    
    final_state = app.invoke(initial_state)
    
    print("\n" + "=" * 50)
    print("Execution Complete")
    print(f"Total Messages: {len(final_state['messages'])}")
