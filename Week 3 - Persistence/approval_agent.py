"""
Week 3: Approval Agent - Human-in-the-Loop Pattern

This agent demonstrates:
1. interrupt_before - Pauses graph before executing a "dangerous" action
2. Checkpointing - Saves state so we can resume after human decision
3. Approval workflow - Agent proposes, human approves/rejects
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Literal, Optional
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# Load .env from parent directory (shared config)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- MOCK ACTION (Would be real email/payment in production) ---
def send_email(to: str, subject: str, body: str) -> str:
    """Simulate sending an email."""
    print(f"\n[EMAIL SENT]")
    print(f"  To: {to}")
    print(f"  Subject: {subject}")
    print(f"  Body: {body[:50]}...")
    return f"Email successfully sent to {to}"

# --- STRUCTURED OUTPUT SCHEMAS ---
class ActionProposal(BaseModel):
    """Agent's proposed action that needs human approval."""
    action_type: Literal["send_email", "no_action"] = Field(
        description="Type of action to perform"
    )
    reasoning: str = Field(description="Why this action is appropriate")
    email_to: Optional[str] = Field(default=None, description="Recipient if sending email")
    email_subject: Optional[str] = Field(default=None)
    email_body: Optional[str] = Field(default=None)

# --- MODEL ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
).with_structured_output(ActionProposal)

# --- STATE ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    proposal: Optional[ActionProposal]  # The proposed action
    human_approved: Optional[bool]       # Human's decision
    result: str                          # Final result

# --- NODES ---
def planner_node(state: AgentState) -> dict:
    """
    Analyzes the request and proposes an action.
    """
    print("\n[PLANNER] Analyzing request...")
    
    messages = state["messages"]
    user_request = messages[0].content
    
    system_prompt = """You are an assistant that helps users with email tasks.
    
Based on the user's request:
1. If they want to send an email, propose the action with recipient, subject, and body.
2. If the request doesn't require an email, set action_type to 'no_action'.

Be specific in your email content - write a complete professional email."""
    
    proposal = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_request)
    ])
    
    print(f"  Proposed Action: {proposal.action_type}")
    if proposal.action_type == "send_email":
        print(f"  To: {proposal.email_to}")
        print(f"  Subject: {proposal.email_subject}")
    
    return {"proposal": proposal}

def approval_gate_node(state: AgentState) -> dict:
    """
    This node exists to be interrupted.
    When we reach here, the graph PAUSES and waits for human input.
    """
    proposal = state["proposal"]
    print("\n" + "=" * 50)
    print("[APPROVAL REQUIRED]")
    print(f"  Action: {proposal.action_type}")
    if proposal.action_type == "send_email":
        print(f"  To: {proposal.email_to}")
        print(f"  Subject: {proposal.email_subject}")
        print(f"  Body Preview: {proposal.email_body[:100] if proposal.email_body else 'N/A'}...")
    print("=" * 50)
    print(">>> Graph is now PAUSED. Resume with approval decision. <<<")
    
    # This node doesn't change state - it's just a checkpoint
    return {}

def executor_node(state: AgentState) -> dict:
    """
    Executes the action IF approved.
    """
    proposal = state["proposal"]
    approved = state.get("human_approved", False)
    
    if not approved:
        print("\n[EXECUTOR] Action REJECTED by human. Skipping.")
        return {"result": "Action was rejected by human. No email sent."}
    
    if proposal.action_type == "send_email":
        result = send_email(
            to=proposal.email_to,
            subject=proposal.email_subject,
            body=proposal.email_body
        )
        return {"result": result}
    
    return {"result": "No action required."}

def response_node(state: AgentState) -> dict:
    """
    Delivers the final response to the user.
    """
    result = state.get("result", "Task completed.")
    print(f"\n[RESPONSE] {result}")
    return {"messages": [AIMessage(content=result)]}

# --- ROUTING ---
def route_after_planner(state: AgentState) -> str:
    proposal = state.get("proposal")
    if proposal and proposal.action_type == "send_email":
        return "needs_approval"
    return "no_approval_needed"

def route_after_approval(state: AgentState) -> str:
    # This runs AFTER human resumes the graph
    approved = state.get("human_approved")
    if approved:
        return "approved"
    return "rejected"

# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("approval_gate", approval_gate_node)
workflow.add_node("executor", executor_node)
workflow.add_node("response", response_node)

# Define edges
workflow.set_entry_point("planner")
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {"needs_approval": "approval_gate", "no_approval_needed": "response"}
)
workflow.add_edge("approval_gate", "executor")  # After approval gate, go to executor
workflow.add_edge("executor", "response")
workflow.add_edge("response", END)

# --- COMPILE WITH CHECKPOINTING AND INTERRUPT ---
checkpointer = MemorySaver()
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["approval_gate"]  # <-- THE KEY: Pause BEFORE this node
)

# --- DEMONSTRATION ---
if __name__ == "__main__":
    import sys
    
    # Thread ID for checkpointing (like a session ID)
    thread_id = "demo-session-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Send a thank you email to john@example.com for the meeting"
    print(f"Request: {query}")
    print("=" * 50)
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "proposal": None,
        "human_approved": None,
        "result": ""
    }
    
    # PHASE 1: Run until interrupt
    print("\n--- PHASE 1: Planning (will pause for approval) ---")
    for event in app.stream(initial_state, config):
        pass
    
    # Check current state
    current_state = app.get_state(config)
    if current_state.next:  # Graph is paused
        print(f"\nGraph paused before: {current_state.next}")
        
        # PHASE 2: Get human input (simulated in this demo)
        print("\n--- PHASE 2: Human Decision ---")
        approval = input("Approve this action? (yes/no): ").strip().lower() == "yes"
        
        # Update state with human's decision
        app.update_state(config, {"human_approved": approval})
        
        # PHASE 3: Resume graph execution
        print(f"\n--- PHASE 3: Resuming with {'APPROVED' if approval else 'REJECTED'} ---")
        for event in app.stream(None, config):
            pass
    
    print("\n" + "=" * 50)
    print("Workflow Complete!")
