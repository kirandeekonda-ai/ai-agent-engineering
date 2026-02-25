# ==============================================================================
# Web Research Module - Tavily Integration
# ==============================================================================
# This module handles web research for market context and competitor analysis.
# Uses Tavily API for intelligent web search with automatic caching.

import os
import hashlib
from typing import Dict, List, Optional
from tavily import TavilyClient as TavilyAPI
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class WebResearchClient:
    """
    Client for performing intelligent web research using Tavily API.
    
    Features:
    - Search for market alternatives and competitors
    - Context-aware caching based on market maturity
    - Token-efficient approach (only searches when valuable)
    """
    
    # Cache duration based on market maturity (in days)
    CACHE_DURATIONS = {
        "stable": 60,      # Gmail, CRM, Excel - barely changes
        "evolving": 21,    # CI/CD, Cloud hosting - new players occasionally
        "fast": 7,         # AI tools, new frameworks - changes weekly
        "trending": 3      # AI agents, RAG - changes daily
    }
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Tavily client.
        
        Args:
            api_key: Tavily API key (reads from env if not provided)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.api_key:
            print("[WARNING] TAVILY_API_KEY not found. Web research disabled.")
            self.client = None
        else:
            self.client = TavilyAPI(api_key=self.api_key)
            print("[OK] Tavily client initialized")
    
    
    def search_competitors(self, query: str, max_results: int = 5) -> Dict:
        """
        Search for competitors and market alternatives.
        
        Args:
            query: Search query (e.g., "sales reporting automation tools pricing")
            max_results: Maximum number of results to return
        
        Returns:
            Dict with:
                - alternatives: List of competitor products
                - sources: List of source URLs
                - raw_results: Full Tavily response
        """
        if not self.client:
            return {"alternatives": [], "sources": [], "error": "Tavily not configured"}
        
        try:
            # Search with Tavily
            response = self.client.search(
                query=f"{query} tools software pricing alternatives 2025",
                search_depth="basic",  # Use "advanced" for deeper research
                max_results=max_results,
                include_answer=True,
                include_domains=["g2.com", "capterra.com", "productboard.com", 
                                "techcrunch.com", "producthunt.com"]
            )
            
            # Extract alternatives from results
            alternatives = []
            sources = []
            
            for result in response.get("results", []):
                sources.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:200]
                })
            
            return {
                "answer": response.get("answer", ""),
                "sources": sources,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Tavily search error: {e}")
            return {"alternatives": [], "sources": [], "error": str(e)}
    
    
    def get_cache_duration(self, market_maturity: str) -> int:
        """
        Get cache duration in days based on market maturity.
        
        Args:
            market_maturity: One of: stable, evolving, fast, trending
        
        Returns:
            Number of days to cache results
        """
        return self.CACHE_DURATIONS.get(market_maturity.lower(), 21)


def get_web_research_client() -> WebResearchClient:
    """
    Create and return a WebResearchClient instance.
    
    Returns:
        WebResearchClient: Initialized client ready to use
    """
    return WebResearchClient()


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================
# from web_research import get_web_research_client
#
# client = get_web_research_client()
# results = client.search_competitors("automated sales reporting")
# print(results)
