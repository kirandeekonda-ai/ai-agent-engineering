"""
Week 9: Production Monitoring

This script demonstrates:
1. A/B testing different prompts
2. Online quality scoring
3. Quality alerts
4. Metrics dashboard
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import time
import random
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Literal

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- PROMPT VARIANTS (A/B Testing) ---
PROMPT_VARIANTS = {
    "A": {
        "name": "concise",
        "system_prompt": "You are a helpful assistant. Be extremely concise - one sentence max."
    },
    "B": {
        "name": "detailed", 
        "system_prompt": "You are a helpful assistant. Provide detailed, comprehensive answers with examples."
    }
}

# --- MODELS ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- PRODUCTION METRICS ---
@dataclass
class RequestMetrics:
    timestamp: str
    variant: str
    query: str
    response: str
    latency_ms: int
    token_count: int
    word_count: int
    quality_score: float  # 0-1

class ProductionMonitor:
    def __init__(self, log_file: str = "production_logs.json"):
        self.log_path = Path(__file__).parent / log_file
        self.metrics: list[RequestMetrics] = []
        self.quality_threshold = 0.7
        self.alert_count = 0
        
        # Load existing logs
        if self.log_path.exists():
            with open(self.log_path) as f:
                data = json.load(f)
                self.metrics = [RequestMetrics(**m) for m in data]
    
    def get_variant(self) -> str:
        """A/B routing - 50/50 split."""
        return random.choice(["A", "B"])
    
    def score_response(self, query: str, response: str) -> float:
        """Simple quality heuristics (in production, use LLM judge)."""
        score = 1.0
        
        # Penalize very short responses
        if len(response) < 10:
            score -= 0.3
        
        # Penalize "I don't know" type responses
        if any(phrase in response.lower() for phrase in ["i don't know", "i cannot", "i'm not sure"]):
            score -= 0.2
        
        # Reward responses that reference the query terms
        query_terms = query.lower().split()
        matches = sum(1 for term in query_terms if term in response.lower())
        score += min(0.2, matches * 0.05)
        
        return max(0.0, min(1.0, score))
    
    def check_alert(self, metrics: RequestMetrics):
        """Check if quality dropped below threshold."""
        if metrics.quality_score < self.quality_threshold:
            self.alert_count += 1
            print(f"\n[ALERT] Low quality response detected!")
            print(f"  Variant: {metrics.variant}")
            print(f"  Score: {metrics.quality_score}")
            print(f"  Query: {metrics.query[:50]}...")
    
    def process_request(self, query: str) -> dict:
        """Process a request with monitoring."""
        start_time = time.time()
        
        # A/B routing
        variant = self.get_variant()
        prompt_config = PROMPT_VARIANTS[variant]
        
        print(f"\n[REQUEST] Variant {variant} ({prompt_config['name']})")
        print(f"  Query: {query[:50]}...")
        
        # Generate response
        response = llm.invoke([
            SystemMessage(content=prompt_config["system_prompt"]),
            HumanMessage(content=query)
        ])
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        response_text = response.content
        word_count = len(response_text.split())
        
        # Estimate tokens (rough)
        token_count = len(query.split()) + word_count + 20  # +20 for system prompt
        
        # Score quality
        quality_score = self.score_response(query, response_text)
        
        # Create metrics record
        metrics = RequestMetrics(
            timestamp=datetime.now().isoformat(),
            variant=variant,
            query=query,
            response=response_text,
            latency_ms=latency_ms,
            token_count=token_count,
            word_count=word_count,
            quality_score=quality_score
        )
        
        self.metrics.append(metrics)
        
        # Check for alerts
        self.check_alert(metrics)
        
        print(f"  Response: {response_text[:60]}...")
        print(f"  Latency: {latency_ms}ms | Words: {word_count} | Quality: {quality_score:.2f}")
        
        return {
            "response": response_text,
            "variant": variant,
            "metrics": asdict(metrics)
        }
    
    def save_logs(self):
        """Persist logs to file."""
        with open(self.log_path, "w") as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2)
        print(f"\nLogs saved to: {self.log_path}")
    
    def get_ab_comparison(self) -> dict:
        """Compare A vs B performance."""
        a_metrics = [m for m in self.metrics if m.variant == "A"]
        b_metrics = [m for m in self.metrics if m.variant == "B"]
        
        def avg(lst, attr):
            if not lst:
                return 0
            return sum(getattr(m, attr) for m in lst) / len(lst)
        
        return {
            "A": {
                "name": PROMPT_VARIANTS["A"]["name"],
                "count": len(a_metrics),
                "avg_latency_ms": round(avg(a_metrics, "latency_ms")),
                "avg_words": round(avg(a_metrics, "word_count")),
                "avg_quality": round(avg(a_metrics, "quality_score"), 3)
            },
            "B": {
                "name": PROMPT_VARIANTS["B"]["name"],
                "count": len(b_metrics),
                "avg_latency_ms": round(avg(b_metrics, "latency_ms")),
                "avg_words": round(avg(b_metrics, "word_count")),
                "avg_quality": round(avg(b_metrics, "quality_score"), 3)
            }
        }
    
    def print_dashboard(self):
        """Print monitoring dashboard."""
        print("\n" + "=" * 60)
        print("PRODUCTION MONITORING DASHBOARD")
        print("=" * 60)
        
        total = len(self.metrics)
        if total == 0:
            print("No data yet")
            return
        
        # Overall stats
        avg_latency = sum(m.latency_ms for m in self.metrics) / total
        avg_quality = sum(m.quality_score for m in self.metrics) / total
        low_quality = sum(1 for m in self.metrics if m.quality_score < self.quality_threshold)
        
        print(f"\nOverall Stats (n={total}):")
        print(f"  Avg Latency:    {avg_latency:.0f}ms")
        print(f"  Avg Quality:    {avg_quality:.2f}")
        print(f"  Low Quality:    {low_quality} ({low_quality/total*100:.1f}%)")
        print(f"  Alerts:         {self.alert_count}")
        
        # A/B comparison
        comparison = self.get_ab_comparison()
        print(f"\nA/B Test Results:")
        print(f"  {'Metric':<15} {'A (concise)':<15} {'B (detailed)':<15} {'Winner':<10}")
        print(f"  {'-'*55}")
        
        a, b = comparison["A"], comparison["B"]
        
        # Latency (lower is better)
        latency_winner = "A" if a["avg_latency_ms"] < b["avg_latency_ms"] else "B"
        print(f"  {'Latency':<15} {a['avg_latency_ms']}ms{'':<10} {b['avg_latency_ms']}ms{'':<10} {latency_winner}")
        
        # Words
        print(f"  {'Words':<15} {a['avg_words']:<15} {b['avg_words']:<15}")
        
        # Quality (higher is better)
        quality_winner = "A" if a["avg_quality"] > b["avg_quality"] else "B"
        print(f"  {'Quality':<15} {a['avg_quality']:<15} {b['avg_quality']:<15} {quality_winner}")
        
        print(f"\n  Sample Size:    A={a['count']}, B={b['count']}")

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    monitor = ProductionMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        # Show dashboard only
        monitor.print_dashboard()
    elif len(sys.argv) > 1 and sys.argv[1] == "simulate":
        # Simulate production traffic
        print("Simulating production traffic...")
        test_queries = [
            "What is Python?",
            "Explain machine learning",
            "How do I cook pasta?",
            "What is the speed of light?",
            "Name the planets in our solar system",
            "What is REST API?",
            "How does encryption work?",
            "What is climate change?"
        ]
        
        for query in test_queries:
            monitor.process_request(query)
            time.sleep(0.5)  # Simulate realistic traffic
        
        monitor.save_logs()
        monitor.print_dashboard()
    else:
        # Single query
        query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is AI?"
        monitor.process_request(query)
        monitor.save_logs()
        monitor.print_dashboard()
