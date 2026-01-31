"""
Week 6: API Orchestrator

This agent demonstrates tool composition:
- Multiple external APIs as tools
- Agent decides which tools to call
- Synthesizes answers from multiple sources
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Optional
import operator
import requests

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from tavily import TavilyClient

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- TOOL 1: WEATHER API (OpenMeteo - free, no key needed) ---
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city. Use this when user asks about weather."""
    print(f"    [Weather API] Getting weather for: {city}", flush=True)
    
    # First, geocode the city
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    try:
        geo_resp = requests.get(geo_url, timeout=5)
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            return f"City '{city}' not found"
        
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        name = geo_data["results"][0]["name"]
        
        # Get weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
        weather_resp = requests.get(weather_url, timeout=5)
        weather_data = weather_resp.json()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        
        return f"{name}: Temperature {temp}C, Wind {wind} km/h"
    except Exception as e:
        return f"Weather API error: {str(e)}"

# --- TOOL 2: STOCK API (Mock data for demo) ---
@tool
def get_stock(symbol: str) -> str:
    """Get stock price and info. Use this when user asks about stocks or investments."""
    print(f"    [Stock API] Getting stock data for: {symbol}", flush=True)
    
    # Mock data (in production, use Alpha Vantage, Yahoo Finance, etc.)
    mock_stocks = {
        "AAPL": {"price": 185.50, "change": "+1.2%", "name": "Apple Inc."},
        "GOOGL": {"price": 142.30, "change": "-0.5%", "name": "Alphabet Inc."},
        "MSFT": {"price": 378.90, "change": "+0.8%", "name": "Microsoft Corp."},
        "NVDA": {"price": 186.10, "change": "+2.1%", "name": "NVIDIA Corp."},
        "TSLA": {"price": 248.50, "change": "-1.3%", "name": "Tesla Inc."},
        "NXT": {"price": 42.75, "change": "+3.5%", "name": "NextPower Inc."},
    }
    
    symbol = symbol.upper()
    if symbol in mock_stocks:
        data = mock_stocks[symbol]
        return f"{data['name']} ({symbol}): ${data['price']} ({data['change']})"
    return f"Stock {symbol} not found in database"

# --- TOOL 3: NEWS API (Tavily) ---
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

@tool
def get_news(topic: str) -> str:
    """Search for recent news on a topic. Use this for current events or market news."""
    print(f"    [News API] Searching news for: {topic}", flush=True)
    try:
        response = tavily_client.search(query=f"{topic} news", max_results=3)
        results = response.get("results", [])
        if results:
            return "\n".join([
                f"- {r.get('title', 'N/A')}"
                for r in results[:3]
            ])
        return "No news found."
    except Exception as e:
        return f"News API error: {str(e)}"

# --- ALL TOOLS ---
tools = [get_weather, get_stock, get_news]

# --- MODEL ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

# Bind tools to model
llm_with_tools = llm.bind_tools(tools)

# --- STATE ---
class OrchestratorState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

# --- NODES ---
def agent_node(state: OrchestratorState) -> dict:
    """The agent decides which tools to call."""
    print("\n[AGENT] Thinking...", flush=True)
    
    messages = state["messages"]
    
    # Add system message if not present
    if not any(isinstance(m, SystemMessage) for m in messages):
        system_msg = SystemMessage(content="""You are a helpful assistant with access to tools.
When you receive tool results, synthesize them into a clear, helpful response for the user.
Always include the actual data from the tools in your final answer.""")
        messages = [system_msg] + messages
    
    response = llm_with_tools.invoke(messages)
    
    if response.tool_calls:
        print(f"    Calling {len(response.tool_calls)} tool(s): {[tc['name'] for tc in response.tool_calls]}")
    else:
        print("    No tools needed, generating response")
    
    return {"messages": [response]}

# Tool node automatically executes tool calls
tool_node = ToolNode(tools)

def should_continue(state: OrchestratorState) -> str:
    """Check if we should continue calling tools or finish."""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

# --- BUILD GRAPH ---
workflow = StateGraph(OrchestratorState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")  # After tools, back to agent

app = workflow.compile()

# --- RUN ---
if __name__ == "__main__":
    import sys
    
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What's the weather in Tokyo and how is NXT stock doing?"
    
    print("=" * 60)
    print(f"USER: {query}")
    print("=" * 60)
    
    result = app.invoke({
        "messages": [HumanMessage(content=query)]
    })
    
    print("\n" + "=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print(result["messages"][-1].content)
