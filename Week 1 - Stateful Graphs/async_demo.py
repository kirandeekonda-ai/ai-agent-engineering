import asyncio
import time

# --- 1. THE CONCEPT ---
# Think of "Async" like a chef in a kitchen.
# SYNCHRONOUS (Blocking): The chef puts bread in the toaster and STARES at it for 2 minutes. 
#                         They do nothing else until the toast pops.
# ASYNCHRONOUS (Non-Blocking): The chef puts bread in the toaster, then chops veggies while the toast cooks.

# --- 2. SIMULATION ---

def mock_llm_call_sync(id):
    """Simulates a slow LLM call (Blocking)"""
    print(f"[{id}] Sending request... (Waiting 2s)")
    time.sleep(2)  # <--- The CPU blocks here. It cannot do anything else.
    print(f"[{id}] Response received!")

async def mock_llm_call_async(id):
    """Simulates a slow LLM call (Non-Blocking)"""
    print(f"[{id}] Sending request... (Waiting 2s)")
    await asyncio.sleep(2)  # <--- The CPU is free! It goes to handle the next task.
    print(f"[{id}] Response received!")

# --- 3. EXECUTION ---

def run_sync():
    print("\n--- SYNCHRONOUS (Sequential) ---")
    start = time.perf_counter()
    mock_llm_call_sync("A")
    mock_llm_call_sync("B")
    mock_llm_call_sync("C")
    end = time.perf_counter()
    print(f"TOTAL TIME: {end - start:.2f} seconds")

async def run_async():
    print("\n--- ASYNCHRONOUS (Concurrent) ---")
    start = time.perf_counter()
    # We schedule all 3 to run "at the same time"
    await asyncio.gather(
        mock_llm_call_async("A"),
        mock_llm_call_async("B"),
        mock_llm_call_async("C")
    )
    end = time.perf_counter()
    print(f"TOTAL TIME: {end - start:.2f} seconds")

if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
