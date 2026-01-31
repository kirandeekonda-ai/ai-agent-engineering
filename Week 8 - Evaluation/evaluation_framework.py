"""
Week 8: Evaluation & Testing

This script demonstrates:
1. Creating evaluation datasets
2. Building custom evaluators
3. Running batch evaluations
4. Analyzing results
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from typing import Callable
from dataclasses import dataclass

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import Client

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- 1. EVALUATION DATASET ---
# In production, these would be curated from real user interactions

EVAL_DATASET = [
    {
        "input": "What is the capital of France?",
        "expected": "Paris",
        "category": "factual"
    },
    {
        "input": "What is 15 + 27?",
        "expected": "42",
        "category": "math"
    },
    {
        "input": "Name three primary colors.",
        "expected": ["red", "blue", "yellow"],
        "category": "factual"
    },
    {
        "input": "Is the Earth flat or round?",
        "expected": "round",
        "category": "factual"
    },
    {
        "input": "What programming language is known for AI/ML?",
        "expected": "Python",
        "category": "technical"
    }
]

# --- 2. THE SYSTEM TO EVALUATE ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

def get_answer(question: str) -> str:
    """The function we're evaluating."""
    response = llm.invoke([
        SystemMessage(content="Answer concisely and directly."),
        HumanMessage(content=question)
    ])
    return response.content

# --- 3. EVALUATORS ---
@dataclass
class EvalResult:
    passed: bool
    score: float
    reason: str

def exact_match_evaluator(output: str, expected: str) -> EvalResult:
    """Check if expected value appears in output."""
    if isinstance(expected, list):
        matches = sum(1 for exp in expected if exp.lower() in output.lower())
        score = matches / len(expected)
        passed = score >= 0.66  # At least 2/3 matched
        return EvalResult(
            passed=passed,
            score=score,
            reason=f"{matches}/{len(expected)} items found"
        )
    else:
        passed = expected.lower() in output.lower()
        return EvalResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            reason="Exact match" if passed else "No match"
        )

def length_evaluator(output: str, max_words: int = 50) -> EvalResult:
    """Check if response is concise."""
    word_count = len(output.split())
    passed = word_count <= max_words
    return EvalResult(
        passed=passed,
        score=min(1.0, max_words / max(word_count, 1)),
        reason=f"{word_count} words (max: {max_words})"
    )

def llm_judge_evaluator(question: str, output: str, expected: str) -> EvalResult:
    """Use LLM to judge correctness (more flexible than exact match)."""
    judge_prompt = f"""You are evaluating an AI response.

Question: {question}
Expected Answer: {expected}
Actual Answer: {output}

Is the actual answer correct? Reply with only: CORRECT or INCORRECT"""

    response = llm.invoke([HumanMessage(content=judge_prompt)])
    passed = "CORRECT" in response.content.upper()
    return EvalResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=response.content.strip()
    )

# --- 4. RUN EVALUATION ---
def run_evaluation(dataset: list, use_llm_judge: bool = False) -> dict:
    """Run evaluation across the dataset."""
    print("\n" + "=" * 60)
    print("EVALUATION RUN")
    print("=" * 60)
    
    results = []
    
    for i, item in enumerate(dataset, 1):
        question = item["input"]
        expected = item["expected"]
        category = item.get("category", "general")
        
        print(f"\n[{i}/{len(dataset)}] {question[:50]}...")
        
        # Get model output
        output = get_answer(question)
        print(f"    Output: {output[:60]}...")
        
        # Run evaluators
        if use_llm_judge:
            correctness = llm_judge_evaluator(question, output, str(expected))
        else:
            correctness = exact_match_evaluator(output, expected)
        
        conciseness = length_evaluator(output)
        
        result = {
            "question": question,
            "expected": expected,
            "output": output,
            "category": category,
            "correctness": {
                "passed": correctness.passed,
                "score": correctness.score,
                "reason": correctness.reason
            },
            "conciseness": {
                "passed": conciseness.passed,
                "score": conciseness.score,
                "reason": conciseness.reason
            }
        }
        results.append(result)
        
        status = "PASS" if correctness.passed else "FAIL"
        print(f"    [{status}] {correctness.reason}")
    
    # Aggregate results
    total = len(results)
    correct = sum(1 for r in results if r["correctness"]["passed"])
    concise = sum(1 for r in results if r["conciseness"]["passed"])
    avg_score = sum(r["correctness"]["score"] for r in results) / total
    
    summary = {
        "total_tests": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1),
        "concise": concise,
        "avg_score": round(avg_score, 3),
        "by_category": {}
    }
    
    # Group by category
    categories = set(r["category"] for r in results)
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_correct = sum(1 for r in cat_results if r["correctness"]["passed"])
        summary["by_category"][cat] = {
            "total": len(cat_results),
            "correct": cat_correct,
            "accuracy": round(cat_correct / len(cat_results) * 100, 1)
        }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests:  {summary['total_tests']}")
    print(f"Correct:      {summary['correct']}/{summary['total_tests']}")
    print(f"Accuracy:     {summary['accuracy']}%")
    print(f"Concise:      {summary['concise']}/{summary['total_tests']}")
    print(f"\nBy Category:")
    for cat, stats in summary["by_category"].items():
        print(f"  {cat}: {stats['accuracy']}% ({stats['correct']}/{stats['total']})")
    
    return {"summary": summary, "results": results}

# --- 5. SAVE RESULTS ---
def save_results(evaluation: dict, filename: str = "eval_results.json"):
    """Save evaluation results to file."""
    filepath = Path(__file__).parent / filename
    with open(filepath, "w") as f:
        json.dump(evaluation, f, indent=2)
    print(f"\nResults saved to: {filepath}")

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    use_llm_judge = len(sys.argv) > 1 and sys.argv[1] == "llm"
    
    if use_llm_judge:
        print("Using LLM-as-Judge evaluator (more flexible)")
    else:
        print("Using exact match evaluator (strict)")
    
    evaluation = run_evaluation(EVAL_DATASET, use_llm_judge=use_llm_judge)
    save_results(evaluation)
