"""
Database Module - PostgreSQL (Supabase) Version
Handles all database operations using Supabase PostgreSQL
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

# Database connection pool
db_pool = None

def get_encoded_db_url():
    """Get properly URL-encoded database connection string"""
    raw_url = os.getenv("SUPABASE_DB_URL")
    
    if not raw_url:
        raise ValueError("SUPABASE_DB_URL not found in environment variables")
    
    raw_url = raw_url.strip('"').strip("'")
    
    # Check if already encoded
    if "%40" in raw_url or "%2A" in raw_url:
        return raw_url
    
    # Encode password
    if raw_url.startswith("postgresql://"):
        after_protocol = raw_url.replace("postgresql://", "")
        parts = after_protocol.rsplit("@", 1)
        
        if len(parts) == 2:
            user_pass = parts[0]
            host_db = parts[1]
            
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                encoded_password = quote(password, safe='')
                return f"postgresql://{user}:{encoded_password}@{host_db}"
    
    return raw_url

def init_db_pool(min_conn=1, max_conn=10):
    """Initialize database connection pool"""
    global db_pool
    
    if db_pool is None:
        db_url = get_encoded_db_url()
        db_pool = SimpleConnectionPool(min_conn, max_conn, db_url)
        print(f"[DB] Connection pool initialized ({min_conn}-{max_conn} connections)")
    
    return db_pool

def get_connection():
    """Get a connection from the pool"""
    global db_pool
    
    if db_pool is None:
        init_db_pool()
    
    return db_pool.getconn()

def return_connection(conn):
    """Return connection to the pool"""
    global db_pool
    
    if db_pool:
        db_pool.putconn(conn)

def save_idea(idea_data: Dict) -> int:
    """
    Save an idea to PostgreSQL database
    
    Args:
        idea_data: Dictionary containing idea fields
    
    Returns:
        int: ID of the saved idea
    """
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ideas (
                    session_id, title, description, problem_solved,
                    time_estimate, cost_estimate, resources_needed,
                    impact, complexity, domain, status, created_at,
                    market_alternatives, market_maturity, market_summary,
                    market_recommendation, research_sources
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                idea_data.get('session_id'),
                idea_data.get('title'),
                idea_data.get('description'),
                idea_data.get('problem_solved'),
                idea_data.get('time_estimate'),
                idea_data.get('cost_estimate'),
                json.dumps(idea_data.get('resources_needed', [])) if isinstance(idea_data.get('resources_needed'), list) else idea_data.get('resources_needed'),
                idea_data.get('impact'),
                idea_data.get('complexity'),
                idea_data.get('domain'),
                idea_data.get('status', 'pending'),
                datetime.now(),
                json.dumps(idea_data.get('market_alternatives', [])) if isinstance(idea_data.get('market_alternatives'), list) else idea_data.get('market_alternatives'),
                idea_data.get('market_maturity'),
                idea_data.get('market_summary'),
                idea_data.get('market_recommendation'),
                json.dumps(idea_data.get('research_sources', [])) if isinstance(idea_data.get('research_sources'), list) else idea_data.get('research_sources')
            ))
            
            idea_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"[DB] Saved idea #{idea_id}")
            return idea_id
            
    except Exception as e:
        conn.rollback()
        print(f"[DB] Error saving idea: {e}")
        raise
    finally:
        return_connection(conn)

def get_all_ideas(limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
    """
    Retrieve all ideas from database with optional pagination
    
    Args:
        limit: Optional limit on number of ideas to return
        offset: Optional offset for pagination
    
    Returns:
        List of idea dictionaries
    """
    conn = get_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build query with optional LIMIT and OFFSET
            query = "SELECT * FROM ideas ORDER BY created_at DESC"
            params = []
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            if offset is not None:
                query += " OFFSET %s"
                params.append(offset)
            
            if params:
                cursor.execute(query, tuple(params))
            else:
                cursor.execute(query)
            
            ideas = cursor.fetchall()
            
            # Convert RealDictRow to regular dict and handle JSON fields
            result = []
            for idea in ideas:
                idea_dict = dict(idea)
                
                # Parse resources_needed if it's a JSON string
                if isinstance(idea_dict.get('resources_needed'), str):
                    try:
                        idea_dict['resources_needed'] = json.loads(idea_dict['resources_needed'])
                    except:
                        pass
                
                # Convert datetime to string
                if idea_dict.get('created_at'):
                    idea_dict['created_at'] = idea_dict['created_at'].isoformat()
                
                result.append(idea_dict)
            
            return result
            
    except Exception as e:
        print(f"[DB] Error fetching ideas: {e}")
        return []
    finally:
        return_connection(conn)

def get_idea_by_id(idea_id: int) -> Optional[Dict]:
    """Get a specific idea by ID"""
    conn = get_connection()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM ideas WHERE id = %s", (idea_id,))
            idea = cursor.fetchone()
            
            if idea:
                idea_dict = dict(idea)
                
                # Parse JSON fields
                if isinstance(idea_dict.get('resources_needed'), str):
                    try:
                        idea_dict['resources_needed'] = json.loads(idea_dict['resources_needed'])
                    except:
                        pass
                
                if idea_dict.get('created_at'):
                    idea_dict['created_at'] = idea_dict['created_at'].isoformat()
                
                return idea_dict
            
            return None
            
    except Exception as e:
        print(f"[DB] Error fetching idea: {e}")
        return None
    finally:
        return_connection(conn)

def update_idea_status(idea_id: int, status: str) -> bool:
    """Update idea status"""
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ideas 
                SET status = %s 
                WHERE id = %s
            """, (status, idea_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
    except Exception as e:
        conn.rollback()
        print(f"[DB] Error updating status: {e}")
        return False
    finally:
        return_connection(conn)

def get_idea_count() -> int:
    """Get total number of ideas"""
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ideas")
            count = cursor.fetchone()[0]
            return count
            
    except Exception as e:
        print(f"[DB] Error getting count: {e}")
        return 0
    finally:
        return_connection(conn)

def close_db_pool():
    """Close all database connections"""
    global db_pool
    
    if db_pool:
        db_pool.closeall()
        db_pool = None
        print("[DB] Connection pool closed")

# Initialize pool on import
init_db_pool()
