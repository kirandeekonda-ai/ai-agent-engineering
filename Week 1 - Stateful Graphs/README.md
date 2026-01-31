# Week 1: Fundamentals of Stateful Graphs

## The Shift: Chains vs. Graphs
In traditional **LangChain**, you built "Chains" (DAGs - Directed Acyclic Graphs). Execution was linear: Step A -> Step B -> Step C.
In **LangGraph**, you build "Graphs". These can be **Cyclic**: Step A -> Step B -> (Decide) -> Step A.

This cycle is what enables "Agency". An agent can try something, fail, correct itself, and try again.

## Core Concepts

### 1. State (`TypedDict` or `Pydantic`)
The **State** is the "Memory" of your graph. It is a shared data structure that passes between nodes.
- Unlike LangChain (where memory was often a hidden magical object), in LangGraph, state is explicit.
- Every node receives the *current* state, modifies it, and passes it on.

```python
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: list[str]
    current_step: int
    final_answer: str | None
```

### 2. Nodes (Functions)
A **Node** is just a python function.
- Input: The current `State`.
- Output: A dictionary of keys to *update* in the state.

```python
def research_node(state: AgentState):
    # Do work...
    return {"messages": ["Found new data!"]}
```

### 3. Edges (Control Flow)
**Edges** define where to go next.
- **Normal Edge**: Always go from A to B.
- **Conditional Edge**: Go to B or C strictly based on a function (e.g., `should_continue`).

```python
def should_continue(state: AgentState):
    if state["final_answer"]:
        return "end"
    return "continue"
```
