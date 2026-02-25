# ==============================================================================
# Research Cache Module
# ==============================================================================
# SQLite-based cache for web research results with context-aware expiration.
# Avoids redundant API calls by caching based on market maturity.

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import os


# Cache database path (stored alongside main database)
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "research_cache.db")


def get_connection():
    """Get a connection to the cache database."""
    return sqlite3.connect(CACHE_DB_PATH)


def init_cache_db():
    """
    Initialize the research cache database.
    Creates the cache table if it doesn't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE,
            query_text TEXT,
            results_json TEXT,
            market_maturity TEXT,
            created_at TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    # Create index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_query_hash 
        ON research_cache(query_hash)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expires_at 
        ON research_cache(expires_at)
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Research cache database initialized")


def _hash_query(query: str) -> str:
    """Generate a hash for the query to use as cache key."""
    # Normalize: lowercase, strip whitespace
    normalized = query.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def cache_research(query: str, results: Dict, ttl_days: int, market_maturity: str = "evolving") -> bool:
    """
    Cache research results with expiration.
    
    Args:
        query: The search query
        results: The research results to cache
        ttl_days: Time-to-live in days
        market_maturity: Market type for reference
    
    Returns:
        True if cached successfully
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query_hash = _hash_query(query)
        now = datetime.now()
        expires_at = now + timedelta(days=ttl_days)
        
        # Upsert: insert or replace existing
        cursor.execute("""
            INSERT OR REPLACE INTO research_cache 
            (query_hash, query_text, results_json, market_maturity, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            query_hash,
            query,
            json.dumps(results),
            market_maturity,
            now.isoformat(),
            expires_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Cache write error: {e}")
        return False


def get_cached_research(query: str) -> Optional[Dict]:
    """
    Retrieve cached research results if not expired.
    
    Args:
        query: The search query
    
    Returns:
        Cached results dict, or None if not found/expired
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query_hash = _hash_query(query)
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT results_json, expires_at, market_maturity 
            FROM research_cache 
            WHERE query_hash = ? AND expires_at > ?
        """, (query_hash, now))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            results = json.loads(row[0])
            results["_cache_info"] = {
                "expires_at": row[1],
                "market_maturity": row[2],
                "from_cache": True
            }
            return results
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Cache read error: {e}")
        return None


def cleanup_expired():
    """
    Remove expired cache entries.
    Should be called periodically to keep database size manageable.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("DELETE FROM research_cache WHERE expires_at < ?", (now,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"[CLEANUP] Cleaned up {deleted} expired cache entries")
        
        return deleted
        
    except Exception as e:
        print(f"[ERROR] Cache cleanup error: {e}")
        return 0


def get_cache_stats() -> Dict:
    """
    Get cache statistics.
    
    Returns:
        Dict with total entries, expired count, size by maturity
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM research_cache")
        total = cursor.fetchone()[0]
        
        # Active entries
        cursor.execute("SELECT COUNT(*) FROM research_cache WHERE expires_at > ?", (now,))
        active = cursor.fetchone()[0]
        
        # By market maturity
        cursor.execute("""
            SELECT market_maturity, COUNT(*) 
            FROM research_cache 
            WHERE expires_at > ? 
            GROUP BY market_maturity
        """, (now,))
        by_maturity = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_entries": total,
            "active_entries": active,
            "expired_entries": total - active,
            "by_maturity": by_maturity
        }
        
    except Exception as e:
        print(f"[ERROR] Cache stats error: {e}")
        return {}


# Initialize cache on module load
init_cache_db()


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================
# from research_cache import cache_research, get_cached_research, cleanup_expired
#
# # Cache some research
# cache_research("sales reporting tools", {"data": [...]}, ttl_days=60, market_maturity="stable")
#
# # Retrieve later
# results = get_cached_research("sales reporting tools")
# if results:
#     print("Cache hit!", results)
# else:
#     print("Cache miss, need to search")
