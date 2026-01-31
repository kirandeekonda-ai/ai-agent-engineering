from typing import TypedDict, Literal
import random
from langgraph.graph import StateGraph, END

# 1. THE STATE
# This dict is passed between all nodes.
class GraphState(TypedDict):
    number: int
    steps: int
    message: str

# 2. THE NODES
# Nodes perform work and return UPDATES to the state.
def generator_node(state: GraphState):
    """Generates a random number."""
    print(f"--- Generator Node: Current Step {state['steps']} ---")
    return {"number": random.randint(1, 100), "steps": state['steps'] + 1}

def check_number_node(state: GraphState):
    """Checks the number and adds a message."""
    print(f"--- Checker Node: Checking {state['number']} ---")
    msg = "Even" if state['number'] % 2 == 0 else "Odd"
    return {"message": msg}

# 3. CONDITIONAL LOGIC
# Decides which node to go to next.
def should_continue(state: GraphState) -> Literal["check_number", "end"]:
    if state['steps'] >= 3:
        print("--- Limit Reached. Ending. ---")
        return "end"
    return "check_number"

# 4. BUILDING THE GRAPH
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("generate", generator_node)
workflow.add_node("check_number", check_number_node)

# Set entry point
workflow.set_entry_point("generate")

# Add edges
# From 'generate' -> conditionally decide where to go
workflow.add_conditional_edges(
    "generate",
    should_continue,
    {
        "check_number": "check_number",
        "end": END
    }
)

# From 'check_number' -> always go back to 'generate' (Loop)
workflow.add_edge("check_number", "generate")

# Compile
app = workflow.compile()

# 5. EXECUTION
print("\n--- Starting Graph Execution ---")
inputs = {"number": 0, "steps": 0, "message": "START"}
for output in app.stream(inputs):
    # stream() returns a dictionary for each node execution
    # e.g., {'generate': {'number': 42, 'steps': 1}}
    for key, value in output.items():
        print(f"Node '{key}' finished: {value}")
