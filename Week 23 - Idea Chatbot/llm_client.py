# ==============================================================================
# Groq LLM Client - Multi-Model Strategy
# ==============================================================================
# This module handles all interactions with Groq's API.
# It uses different models for different tasks to avoid rate limits.

from groq import Groq
from typing import List, Dict
import os


# ------------------------------------------------------------------------------
# System Prompts - Domain-Specific
# ------------------------------------------------------------------------------
# Different prompts for different industries/departments
# The AI will automatically adapt based on the conversation context

SYSTEM_PROMPTS = {
    "software": """You are an Idea Assistant specializing in software development and tech innovation.

Your role:
- Help engineers articulate technical ideas clearly
- Ask about architecture, scalability, and technical feasibility
- Focus on development time, tech stack, and resources (developers, tools, infrastructure)
- Consider integration with existing systems and technical debt

Key questions to ask:
- What's the tech stack? (languages, frameworks, databases)
- How does it integrate with existing systems?
- What about scalability and performance?
- Development timeline and team size?
- Any DevOps/deployment considerations?

Guidelines: Keep responses concise (2-3 sentences). Be supportive and technical.""",

    "engineering": """You are an Idea Assistant specializing in structural/mechanical/civil engineering.

Your role:
- Help engineers articulate infrastructure and construction ideas
- Ask about safety standards, regulations, and compliance
- Focus on materials, blueprints, construction time, and costs
- Consider environmental impact and structural integrity

Key questions to ask:
- What materials are needed?
- Safety standards and regulations to follow?
- Construction timeline and phases?
- Budget estimate (materials + labor)?
- Environmental or structural impact?

Guidelines: Keep responses concise (2-3 sentences). Be supportive and detail-oriented.""",

    "hr": """You are an Idea Assistant specializing in Human Resources and people operations.

Your role:
- Help HR professionals articulate ideas about employee engagement, hiring, training
- Ask about impact on employee experience and company culture
- Focus on implementation timeline, affected departments, and change management
- Consider legal/compliance aspects

Key questions to ask:
- Who is affected? (employees, managers, departments)
- What problem does it solve for people?
- Timeline for rollout?
- Training or communication needs?
- Budget for programs or tools?

Guidelines: Keep responses concise (2-3 sentences). Be supportive and people-focused.""",

    "finance": """You are an Idea Assistant specializing in Finance and accounting operations.

Your role:
- Help finance professionals articulate ideas about processes, reporting, cost savings
- Ask about ROI, cost-benefit analysis, and financial impact
- Focus on compliance, audit trails, and financial controls
- Consider integration with accounting systems

Key questions to ask:
- What's the expected ROI or cost savings?
- Implementation cost and ongoing expenses?
- Compliance or audit requirements?
- Integration with existing financial systems?
- Timeline and resources needed?

Guidelines: Keep responses concise (2-3 sentences). Be supportive and numbers-focused.""",

    "general": """You are an Idea Assistant for workplace innovation across all departments.

Your role:
- Help employees articulate their ideas clearly
- Ask thoughtful questions about time savings, cost, and resources needed
- Be encouraging and supportive (never dismiss or judge ideas)
- Guide users to think through implementation details

Key questions to ask:
- What problem does it solve?
- Who benefits from this idea?
- What resources are needed (time, money, people)?
- What's the estimated impact?
- Implementation timeline?

Guidelines: Keep responses concise (2-3 sentences). Be conversational, friendly, and encouraging."""
}


# Domain detection keywords
DOMAIN_KEYWORDS = {
    "software": [
        "code", "coding", "app", "application", "api", "database", "frontend", "backend",
        "software", "programming", "developer", "deployment", "server", "cloud",
        "website", "web", "mobile", "algorithm", "script", "automation tool",
        "dashboard", "portal", "interface", "integration", "microservice"
    ],
    "engineering": [
        "structure", "structural", "build", "building", "construction", "materials",
        "safety", "blueprint", "design", "mechanical", "civil", "infrastructure",
        "foundation", "steel", "concrete", "fabrication", "manufacturing",
        "equipment", "machinery", "facility", "plant", "installation"
    ],
    "hr": [
        "employee", "employees", "hiring", "recruitment", "onboarding", "training",
        "performance", "culture", "engagement", "retention", "benefits",
        "compensation", "team building", "morale", "workplace", "staff",
        "talent", "people", "manager", "leadership", "career development"
    ],
    "finance": [
        "budget", "cost", "expense", "accounting", "invoice", "payment",
        "financial", "revenue", "profit", "roi", "savings", "audit",
        "compliance", "reporting", "forecast", "cash flow", "payroll",
        "ledger", "reconciliation", "tax", "procurement", "vendor"
    ]
}


def detect_domain(message: str) -> str:
    """
    Automatically detect the domain/industry based on keywords in the message.
    
    Args:
        message (str): The user's message
    
    Returns:
        str: Detected domain key ("software", "engineering", "hr", "finance", or "general")
    
    Example:
        >>> detect_domain("I want to build a new API for reports")
        'software'
        >>> detect_domain("We need better employee onboarding")
        'hr'
    """
    message_lower = message.lower()
    
    # Count matches for each domain
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        # Count how many keywords from this domain appear in the message
        score = sum(1 for keyword in keywords if keyword in message_lower)
        domain_scores[domain] = score
    
    # Get the domain with the highest score
    best_domain = max(domain_scores.items(), key=lambda x: x[1])
    
    # Only use specialized domain if we have at least 1 keyword match
    if best_domain[1] > 0:
        return best_domain[0]
    
    return "general"


class GroqClient:
    """
    Client for interacting with Groq's LLM API using multiple models.
    
    Strategy:
    - Use fast models for simple conversations
    - Use powerful models for complex reasoning (idea extraction)
    - Use specialized models for quality evaluation
    
    This spreads the load across multiple models to avoid hitting rate limits.
    """
    
    # ------------------------------------------------------------------------------
    # Model Configuration
    # ------------------------------------------------------------------------------
    # Each task uses a different model to balance performance and rate limits
    
    MODELS = {
        "chat": "llama-3.1-8b-instant",
        # Fast model for conversational responses
        # - 14.4K requests per day
        # - 6K tokens per minute
        # Perfect for quick back-and-forth chat
        
        "extract": "meta-llama/llama-4-scout-17b-16e-instruct",
        # Reasoning model for extracting structured data from conversations
        # - 1K requests per day
        # - 6K tokens per minute
        # Better at understanding context and extracting ideas
        
        "evaluate": "meta-llama/llama-guard-4-12b"
        # Specialized model for content evaluation
        # - 14.4K requests per day
        # - 15K tokens per minute
        # Designed for quality checking and moderation
    }
    
    def __init__(self, api_key: str):
        """
        Initialize the Groq client.
        
        Args:
            api_key (str): Your Groq API key from environment variables
        """
        self.client = Groq(api_key=api_key)
    
    
    def chat(self, message: str, conversation_history: List[Dict] = None, detected_domain: str = None) -> str:
        """
        Send a message to the chatbot and get a response.
        
        Uses the fast 'llama-3.1-8b-instant' model for conversational responses.
        Automatically adapts system prompt based on detected domain.
        
        Args:
            message (str): The user's message
            conversation_history (List[Dict], optional): Previous messages in the conversation
                Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            detected_domain (str, optional): Pre-detected domain. If None, will auto-detect.
        
        Returns:
            str: The chatbot's response
        
        Example:
            response = client.chat("I have an idea to automate reports")
        """
        # Build the conversation messages
        messages = conversation_history or []
        
        # Detect domain if not provided and not already in conversation
        if not messages or messages[0].get("role") != "system":
            # Auto-detect domain from the current message
            domain = detected_domain or detect_domain(message)
            
            # Get the appropriate system prompt for this domain
            system_prompt = SYSTEM_PROMPTS.get(domain, SYSTEM_PROMPTS["general"])
            
            # Add system prompt at the beginning
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })
            
            # Log the detected domain for debugging
            if domain != "general":
                print(f"🎯 Detected domain: {domain}")
        
        # Add the current user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Call Groq API with the chat model
            completion = self.client.chat.completions.create(
                model=self.MODELS["chat"],
                messages=messages,
                temperature=0.7,          # Slightly creative but focused
                max_tokens=500,           # Reasonable response length
                top_p=1,
                stream=False
            )
            
            # Extract the response text
            return completion.choices[0].message.content
            
        except Exception as e:
            # Handle errors gracefully
            print(f"Error calling Groq API: {e}")
            return "I'm having trouble connecting right now. Please try again."
    
    
    def extract_idea(self, conversation: List[Dict]) -> Dict:
        """
        Extract a structured idea from a conversation.
        
        Uses the 'llama-4-scout' model for better reasoning and extraction.
        This model is better at understanding context and generating structured output.
        
        Args:
            conversation (List[Dict]): The full conversation history
                Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            Dict: Structured idea with all fields, or error dict if extraction fails
        
        Example:
            idea = client.extract_idea(conversation_history)
            print(idea['title'])  # "Report Automation API"
        """
        
        # Build the extraction prompt
        extraction_system_prompt = """
You are an expert at analyzing conversations and extracting structured information.

Analyze the conversation and extract a structured idea summary.

Return ONLY valid JSON (no markdown code blocks, no explanation, just the JSON object):
{
  "title": "Short, descriptive title (max 10 words)",
  "description": "Clear 2-3 sentence description of the idea",
  "problem_solved": "What problem does this idea solve?",
  "time_estimate": "Estimated development/implementation time",
  "cost_estimate": "Cost range estimate, or 'Unknown' if not discussed",
  "resources_needed": ["List of resources, tools, or people needed"],
  "impact": "Who benefits and how? Quantify if possible.",
  "complexity": "low, medium, or high"
}

Rules:
- If information wasn't discussed, use "Not specified"
- Be concise and clear
- Extract actual quotes when relevant
- Return ONLY the JSON object, nothing else
"""
        
        # Build messages for the API call
        messages = [
            {"role": "system", "content": extraction_system_prompt},
            {"role": "user", "content": f"Here is the conversation to analyze:\n\n{self._format_conversation(conversation)}"}
        ]
        
        try:
            # Use the llama-4-scout model for better reasoning
            completion = self.client.chat.completions.create(
                model=self.MODELS["extract"],
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            # Get the response
            response_text = completion.choices[0].message.content.strip()
            
            # Try to parse as JSON
            import json
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Extract content between ```json and ```
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            
            try:
                idea = json.loads(response_text)
                return idea
            except json.JSONDecodeError:
                # If JSON parsing fails, return an error
                print(f"Failed to parse JSON: {response_text}")
                return {
                    "error": "Failed to extract structured idea",
                    "raw_response": response_text
                }
        
        except Exception as e:
            print(f"Error during idea extraction: {e}")
            return {
                "error": f"Extraction failed: {str(e)}"
            }
    
    
    def _format_conversation(self, conversation: List[Dict]) -> str:
        """
        Format conversation history into readable text for extraction.
        
        Args:
            conversation (List[Dict]): Conversation history
        
        Returns:
            str: Formatted conversation text
        """
        formatted = []
        for msg in conversation:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Skip system messages
            if role == "system":
                continue
            
            # Format as "User: ..." or "Assistant: ..."
            role_label = "User" if role == "user" else "Assistant"
            formatted.append(f"{role_label}: {content}")
        
        return "\n".join(formatted)
    
    
    def check_idea_readiness(self, conversation: List[Dict]) -> Dict:
        """
        Check if the conversation has enough detail to be saved as an idea.
        
        Uses AI to intelligently evaluate conversation depth and completeness.
        No hard rules - the AI decides based on content quality.
        
        Args:
            conversation (List[Dict]): The conversation history
        
        Returns:
            Dict with:
                - ready (bool): True if idea is ready to be saved
                - reason (str): Explanation of the decision
        
        Example:
            result = client.check_idea_readiness(history)
            if result['ready']:
                # Auto-extract and save
        """
        
        # System prompt for readiness evaluation
        readiness_prompt = """
You are an expert evaluator for an idea submission system.

Analyze this conversation and determine if it contains enough information to be saved as a concrete idea.

A conversation is READY if it includes:
1. Clear description of what the idea is
2. What problem it solves or why it's valuable
3. At least ONE of:
   - Who would use it or who benefits
   - Rough time/cost estimate
   - Resources needed
   - Implementation approach

A conversation is NOT READY if:
- It's just initial exploration ("I have an idea")
- Too vague ("make things better")
- Only questions, no concrete idea yet
- Just started the conversation

Respond with ONLY this JSON format (no markdown, no explanation):
{
  "ready": true/false,
  "reason": "Brief explanation why it is or isn't ready"
}
"""
        
        # Format conversation
        formatted_conversation = self._format_conversation(conversation)
        
        # Build messages
        messages = [
            {"role": "system", "content": readiness_prompt},
            {"role": "user", "content": f"Conversation:\n{formatted_conversation}"}
        ]
        
        try:
            # Use llama-4-scout for intelligent evaluation
            completion = self.client.chat.completions.create(
                model=self.MODELS["extract"],  # Use same model as extraction
                messages=messages,
                temperature=0.3,  # Low for consistent evaluation
                max_tokens=200,
                top_p=1,
                stream=False
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            
            # Remove markdown if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            
            try:
                result = json.loads(response_text)
                return {
                    "ready": result.get("ready", False),
                    "reason": result.get("reason", "Unknown")
                }
            except json.JSONDecodeError:
                print(f"Failed to parse readiness response: {response_text}")
                return {
                    "ready": False,
                    "reason": "Failed to evaluate"
                }
        
        except Exception as e:
            print(f"Error checking idea readiness: {e}")
            return {
                "ready": False,
                "reason": f"Error: {str(e)}"
            }
    
    
    def evaluate_idea(self, idea: Dict) -> Dict:
        """
        Evaluate the quality and feasibility of an idea.
        
        Uses the 'llama-guard' model for quality assessment.
        
        Args:
            idea (Dict): The idea to evaluate
        
        Returns:
            Dict: Evaluation results with quality score and suggestions
        
        Note: This is an advanced feature for later
        """
        # TODO: Implement in future lessons if needed
        pass


# ------------------------------------------------------------------------------
# Helper Function to Initialize Client
# ------------------------------------------------------------------------------

def get_groq_client() -> GroqClient:
    """
    Create and return a Groq client instance.
    
    Reads the API key from environment variables.
    
    Returns:
        GroqClient: Initialized client ready to use
    
    Raises:
        ValueError: If GROQ_API_KEY is not set
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in environment variables. "
            "Please create a .env file with your API key."
        )
    
    return GroqClient(api_key)


# ------------------------------------------------------------------------------
# USAGE EXAMPLE
# ------------------------------------------------------------------------------
# from llm_client import get_groq_client
#
# client = get_groq_client()
# response = client.chat("Hello, I have an idea!")
# print(response)
