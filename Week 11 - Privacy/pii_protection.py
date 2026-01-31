"""
Week 11: Data Privacy & PII Protection

This script demonstrates:
1. PII detection (emails, phones, SSN, credit cards, names)
2. Masking sensitive data before LLM processing
3. Audit logging for compliance
4. Privacy-preserving agent wrapper
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import re
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- PII PATTERNS ---
PII_PATTERNS = {
    "email": {
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "replacement": "[EMAIL_REDACTED]"
    },
    "phone": {
        "pattern": r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
        "replacement": "[PHONE_REDACTED]"
    },
    "ssn": {
        "pattern": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        "replacement": "[SSN_REDACTED]"
    },
    "credit_card": {
        "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "replacement": "[CREDIT_CARD_REDACTED]"
    },
    "ip_address": {
        "pattern": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "replacement": "[IP_REDACTED]"
    },
    "date_of_birth": {
        "pattern": r'\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b',
        "replacement": "[DOB_REDACTED]"
    }
}

# --- PII DETECTOR ---
@dataclass
class PIIMatch:
    pii_type: str
    original: str
    position: tuple

@dataclass
class PIIResult:
    has_pii: bool
    matches: list[PIIMatch]
    masked_text: str
    original_text: str

class PIIDetector:
    """Detects and masks PII in text."""
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(config["pattern"], re.IGNORECASE)
            for name, config in PII_PATTERNS.items()
        }
    
    def detect(self, text: str) -> list[PIIMatch]:
        """Detect all PII in text."""
        matches = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    original=match.group(),
                    position=(match.start(), match.end())
                ))
        
        return matches
    
    def mask(self, text: str) -> PIIResult:
        """Detect and mask all PII."""
        matches = self.detect(text)
        masked = text
        
        # Replace in reverse order to maintain positions
        for match in sorted(matches, key=lambda m: m.position[0], reverse=True):
            replacement = PII_PATTERNS[match.pii_type]["replacement"]
            masked = masked[:match.position[0]] + replacement + masked[match.position[1]:]
        
        return PIIResult(
            has_pii=len(matches) > 0,
            matches=matches,
            masked_text=masked,
            original_text=text
        )

# --- AUDIT LOGGER ---
class AuditLogger:
    """Logs PII access for compliance."""
    
    def __init__(self, log_file: str = "audit_log.json"):
        self.log_path = Path(__file__).parent / log_file
        self.logs = []
        
        if self.log_path.exists():
            with open(self.log_path) as f:
                self.logs = json.load(f)
    
    def log_pii_access(self, action: str, pii_types: list[str], user_id: str = "system"):
        """Log PII access event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "pii_types": pii_types,
            "user_id": user_id
        }
        self.logs.append(entry)
        self.save()
        return entry
    
    def save(self):
        """Persist logs."""
        with open(self.log_path, "w") as f:
            json.dump(self.logs, f, indent=2)
    
    def get_recent(self, n: int = 10) -> list:
        """Get recent log entries."""
        return self.logs[-n:]

# --- PRIVACY-PRESERVING AGENT ---
class PrivateAgent:
    """Agent that protects PII before LLM processing."""
    
    def __init__(self):
        self.detector = PIIDetector()
        self.audit = AuditLogger()
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        self.pii_count = 0
    
    def process(self, user_input: str, user_id: str = "anonymous") -> dict:
        """Process input with PII protection."""
        print(f"\n[INPUT] {user_input[:60]}...")
        
        # Detect and mask PII
        result = self.detector.mask(user_input)
        
        if result.has_pii:
            self.pii_count += len(result.matches)
            pii_types = list(set(m.pii_type for m in result.matches))
            
            print(f"  [PII DETECTED] {len(result.matches)} item(s) found:")
            for match in result.matches:
                print(f"    - {match.pii_type}: {match.original[:20]}...")
            
            # Audit log
            self.audit.log_pii_access(
                action="masked_for_llm",
                pii_types=pii_types,
                user_id=user_id
            )
            
            # Use masked text for LLM
            safe_input = result.masked_text
            print(f"  [MASKED] {safe_input[:60]}...")
        else:
            print("  [CLEAN] No PII detected")
            safe_input = user_input
        
        # Process with LLM
        response = self.llm.invoke([
            SystemMessage(content="You are a helpful assistant. If you see [REDACTED] placeholders, acknowledge them professionally."),
            HumanMessage(content=safe_input)
        ])
        
        print(f"  [RESPONSE] {response.content[:60]}...")
        
        return {
            "response": response.content,
            "pii_detected": result.has_pii,
            "pii_count": len(result.matches) if result.has_pii else 0,
            "masked_input": safe_input
        }
    
    def get_stats(self) -> dict:
        """Get privacy statistics."""
        return {
            "total_pii_masked": self.pii_count,
            "audit_entries": len(self.audit.logs)
        }

# --- TEST CASES ---
TEST_INPUTS = [
    ("What is the weather today?", False),
    ("My email is john.doe@example.com, please contact me.", True),
    ("Call me at 555-123-4567 or (555) 987-6543", True),
    ("My SSN is 123-45-6789 and credit card is 4532-1234-5678-9012", True),
    ("I was born on 03/15/1990 in New York", True),
    ("Server IP is 192.168.1.100, please check it", True),
]

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    agent = PrivateAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=" * 60)
        print("PII DETECTION TEST SUITE")
        print("=" * 60)
        
        correct = 0
        for input_text, has_pii in TEST_INPUTS:
            result = agent.process(input_text)
            
            actual = result["pii_detected"]
            status = "PASS" if actual == has_pii else "FAIL"
            if actual == has_pii:
                correct += 1
            
            print(f"  [{status}] Expected PII: {has_pii}, Got: {actual}")
        
        print("\n" + "=" * 60)
        print(f"RESULTS: {correct}/{len(TEST_INPUTS)} correct")
        print("=" * 60)
        
        stats = agent.get_stats()
        print(f"Total PII Masked: {stats['total_pii_masked']}")
        print(f"Audit Entries: {stats['audit_entries']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "audit":
        print("=" * 60)
        print("AUDIT LOG")
        print("=" * 60)
        for entry in agent.audit.get_recent():
            print(f"{entry['timestamp']}: {entry['action']} - {entry['pii_types']}")
    else:
        # Single query
        query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "My email is test@example.com"
        result = agent.process(query)
        
        print("\n" + "=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(result["response"])
