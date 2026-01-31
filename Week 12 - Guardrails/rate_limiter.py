"""
Week 12: Rate Limiting & Guardrails

This script demonstrates:
1. Token budget management (per user/session)
2. Request rate limiting
3. Output content guardrails
4. Cost controls
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import time
import re
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- TOKEN BUDGET ---
@dataclass
class UserBudget:
    user_id: str
    max_tokens: int = 10000  # Daily limit
    used_tokens: int = 0
    max_requests: int = 50   # Requests per hour
    request_count: int = 0
    reset_time: datetime = field(default_factory=datetime.now)
    
    def check_reset(self):
        """Reset counters if time has passed."""
        now = datetime.now()
        # Reset daily token budget at midnight
        if now.date() > self.reset_time.date():
            self.used_tokens = 0
            self.reset_time = now
        # Reset hourly request count
        if now - self.reset_time > timedelta(hours=1):
            self.request_count = 0
            self.reset_time = now
    
    def can_make_request(self, estimated_tokens: int = 100) -> tuple[bool, str]:
        """Check if user can make a request."""
        self.check_reset()
        
        if self.request_count >= self.max_requests:
            return False, f"Rate limit exceeded ({self.max_requests}/hour)"
        
        if self.used_tokens + estimated_tokens > self.max_tokens:
            remaining = self.max_tokens - self.used_tokens
            return False, f"Token budget exceeded ({remaining} remaining of {self.max_tokens})"
        
        return True, "OK"
    
    def record_usage(self, tokens: int):
        """Record token usage."""
        self.used_tokens += tokens
        self.request_count += 1

class BudgetManager:
    """Manages budgets for multiple users."""
    
    def __init__(self):
        self.budgets: dict[str, UserBudget] = {}
    
    def get_budget(self, user_id: str) -> UserBudget:
        """Get or create user budget."""
        if user_id not in self.budgets:
            self.budgets[user_id] = UserBudget(user_id=user_id)
        return self.budgets[user_id]
    
    def check_limits(self, user_id: str, estimated_tokens: int = 100) -> tuple[bool, str]:
        """Check if user is within limits."""
        budget = self.get_budget(user_id)
        return budget.can_make_request(estimated_tokens)
    
    def record(self, user_id: str, tokens: int):
        """Record usage."""
        budget = self.get_budget(user_id)
        budget.record_usage(tokens)

# --- OUTPUT GUARDRAILS ---
BLOCKED_PATTERNS = [
    # Violence/harm
    r'\b(kill|murder|attack|bomb|weapon)\b.*\b(how|instructions|steps)\b',
    r'\b(suicide|self[-\s]?harm)\b',
    
    # Illegal activities
    r'\b(hack|crack|bypass)\b.*\b(password|security|account)\b',
    r'\b(drugs?|cocaine|heroin)\b.*\b(make|create|synthesize)\b',
    
    # Explicit content
    r'\bexplicit\s+(sexual|content)\b',
]

TOXICITY_KEYWORDS = [
    "hate", "racist", "sexist", "discriminate", "slur"
]

@dataclass
class GuardrailResult:
    passed: bool
    issues: list[str]
    filtered_output: Optional[str]

class OutputGuardrails:
    """Filter and validate LLM outputs."""
    
    def __init__(self):
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS
        ]
    
    def check_blocked_patterns(self, text: str) -> list[str]:
        """Check for blocked content patterns."""
        issues = []
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                issues.append(f"Blocked pattern detected")
        return issues
    
    def check_toxicity(self, text: str) -> list[str]:
        """Simple toxicity check (in production, use a classifier)."""
        issues = []
        text_lower = text.lower()
        for keyword in TOXICITY_KEYWORDS:
            if keyword in text_lower:
                issues.append(f"Potential toxicity: '{keyword}'")
        return issues
    
    def check_length(self, text: str, max_length: int = 2000) -> list[str]:
        """Check output length."""
        if len(text) > max_length:
            return [f"Output too long ({len(text)} > {max_length})"]
        return []
    
    def validate(self, text: str) -> GuardrailResult:
        """Run all guardrail checks."""
        issues = []
        
        issues.extend(self.check_blocked_patterns(text))
        issues.extend(self.check_toxicity(text))
        issues.extend(self.check_length(text))
        
        passed = len(issues) == 0
        filtered = text if passed else "[Response blocked by guardrails]"
        
        return GuardrailResult(
            passed=passed,
            issues=issues,
            filtered_output=filtered
        )

# --- GUARDED AGENT ---
class GuardedAgent:
    """Agent with rate limiting and output guardrails."""
    
    def __init__(self):
        self.budget_manager = BudgetManager()
        self.guardrails = OutputGuardrails()
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        self.blocked_count = 0
        self.total_count = 0
    
    def process(self, query: str, user_id: str = "default") -> dict:
        """Process query with all protections."""
        self.total_count += 1
        
        print(f"\n[USER: {user_id}] {query[:50]}...")
        
        # Check rate limits
        can_proceed, reason = self.budget_manager.check_limits(user_id)
        if not can_proceed:
            self.blocked_count += 1
            print(f"  [BLOCKED] {reason}")
            return {
                "blocked": True,
                "reason": reason,
                "response": None
            }
        
        # Generate response
        response = self.llm.invoke([
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=query)
        ])
        
        output = response.content
        
        # Estimate tokens used
        tokens_used = len(query.split()) + len(output.split()) + 20
        
        # Check output guardrails
        guardrail_result = self.guardrails.validate(output)
        
        if not guardrail_result.passed:
            self.blocked_count += 1
            print(f"  [GUARDRAIL] Issues: {guardrail_result.issues}")
            output = guardrail_result.filtered_output
        else:
            print(f"  [OK] Response: {output[:50]}...")
        
        # Record usage
        self.budget_manager.record(user_id, tokens_used)
        budget = self.budget_manager.get_budget(user_id)
        
        print(f"  [USAGE] {tokens_used} tokens | Total: {budget.used_tokens}/{budget.max_tokens} | Requests: {budget.request_count}/{budget.max_requests}")
        
        return {
            "blocked": not guardrail_result.passed,
            "response": output,
            "tokens_used": tokens_used,
            "remaining_tokens": budget.max_tokens - budget.used_tokens
        }
    
    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            "total_requests": self.total_count,
            "blocked": self.blocked_count,
            "block_rate": round(self.blocked_count / max(self.total_count, 1) * 100, 1)
        }

# --- TEST ---
def run_test_suite():
    """Test rate limiting and guardrails."""
    print("=" * 60)
    print("RATE LIMITING & GUARDRAILS TEST")
    print("=" * 60)
    
    agent = GuardedAgent()
    
    # Test 1: Normal requests
    print("\n--- Test 1: Normal Requests ---")
    agent.process("What is Python?", "user1")
    agent.process("Explain machine learning", "user1")
    
    # Test 2: Different users have separate budgets
    print("\n--- Test 2: Separate User Budgets ---")
    agent.process("What is AI?", "user2")
    
    # Test 3: Guardrail test (safe query about security)
    print("\n--- Test 3: Safe Security Question ---")
    agent.process("What are best practices for password security?", "user1")
    
    # Test 4: Rapid requests (rate limit test)
    print("\n--- Test 4: Multiple Rapid Requests ---")
    for i in range(3):
        agent.process(f"Quick question {i+1}", "user3")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    stats = agent.get_stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Blocked: {stats['blocked']} ({stats['block_rate']}%)")
    
    # Show user budgets
    print("\nUser Budgets:")
    for user_id, budget in agent.budget_manager.budgets.items():
        print(f"  {user_id}: {budget.used_tokens}/{budget.max_tokens} tokens, {budget.request_count}/{budget.max_requests} requests")

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_test_suite()
    else:
        agent = GuardedAgent()
        query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is rate limiting?"
        result = agent.process(query, "demo_user")
        
        print("\n" + "=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        if result["response"]:
            print(result["response"])
        print(f"\nTokens used: {result.get('tokens_used', 0)}")
        print(f"Remaining: {result.get('remaining_tokens', 0)}")
