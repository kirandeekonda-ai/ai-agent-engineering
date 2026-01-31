import os
import operator
from typing import Annotated, TypedDict, Union

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# 1. SETUP ENV
load_dotenv()

from langchain_community.tools import TavilySearchResults

# 2. DEFINE TOOLS
# Real Internet Search (Tavily)
# max_results=1 ensures we don't start with burning credits
search = TavilySearchResults(max_results=1)
tools = [search]

# 3. DEFINE MODEL (GROQ)
# leveraging the free tier model
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
).bind_tools(tools)

# 4. DEFINE STATE
class AgentState(TypedDict):
    # 'messages' is a list of ANY message type (Human, AI, Tool)
    # operator.add means "append to list" instead of "overwrite"
    messages: Annotated[list[BaseMessage], operator.add]

# 5. DEFINE NODES

def reason_node(state: AgentState):
    """
    The 'Brain' of the agent. Decides what to do next.
    Input: Full message history
    Output: The LLM's next response (either text OR a tool call)
    """
    print("\n--- AGENT: Reasoning ---")
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Note: We don't need a custom 'action_node' because LangGraph has a prebuilt 'ToolNode'
# that automatically executes tools if the LLM requests them!
tool_node = ToolNode(tools)

# 6. CONDITIONAL LOGIC
def should_continue(state: AgentState):
    """
    Checks the last message.
    Decides to continue to tools, end, or force stop (Circuit Breaker).
    """
    last_message = state["messages"][-1]
    
    # CIRCUIT BREAKER (Safety Pattern)
    # If the conversation is getting too long (e.g., > 6 messages), force it to stop.
    if len(state["messages"]) > 6:
        print("\n--- CIRCUIT BREAKER ENABLED: Max steps reached ---")
        return "end"
    
    if last_message.tool_calls:
        return "tools"
    return "end"

# 7. BUILD GRAPH
workflow = StateGraph(AgentState)

workflow.add_node("agent", reason_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

# If we run a tool, we ALWAYS go back to the agent to read the result
workflow.add_edge("tools", "agent")

app = workflow.compile()

import sys

# ...

# 8. EXECUTION LOOP
if __name__ == "__main__":
    print("Welcome to the Groq Research Agent!")
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"Query received from CLI: {query}")
    else:
        query = input("What do you want to research? ")
    
    # SYSTEM PROMPT INJECTION: Llama 3 on Groq sometimes struggles with tool syntax.
    # We explicitly tell it how to behave.
    sys_msg = """You are a helpful research assistant. 
    You have access to a search tool. 
    If you need facts, YOU MUST CALL the result tool.
    Do not guess. Use the tool."""

    initial_state = {"messages": [
        SystemMessage(content=sys_msg),
        HumanMessage(content=query)
    ]}
    
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"\n--- Node '{key}' Finished ---")
            # Value is the STATE update. It contains 'messages'.
            # We want to print the LAST message added.
            if "messages" in value:
                last_msg = value["messages"][-1]
                print(f"OUTPUT: {last_msg.content}")
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    print(f"TOOL CALLS: {last_msg.tool_calls}")
