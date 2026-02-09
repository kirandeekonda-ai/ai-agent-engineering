"""
Supabase Database Migration Script - Fixed URL Encoding
Creates tables in PostgreSQL (Supabase)
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import quote  # Use quote, not quote_plus!

# Load environment variables
load_dotenv()

def get_encoded_db_url():
    """
    Get and properly encode database URL
    Uses urllib.parse.quote to encode special characters in password
    
    Special characters encoding:
    @ -> %40
    * -> %2A  
    + -> %2B
    """
    raw_url = os.getenv("SUPABASE_DB_URL")
    
    if not raw_url:
        raise ValueError("SUPABASE_DB_URL not found in .env file")
    
    # Remove surrounding quotes if present
    raw_url = raw_url.strip('"').strip("'")
    
    # Check if already encoded (contains %40, %2A, etc.)
    if "%40" in raw_url or "%2A" in raw_url or "%2B" in raw_url:
        print("[INFO] URL appears already encoded")
        return raw_url
    
    # Parse and encode password
    if raw_url.startswith("postgresql://"):
        # Split into parts: postgresql://user:password@host:port/db
        after_protocol = raw_url.replace("postgresql://", "")
        
        # Find the first @ which separates user:password from host
        # But we need to be careful because password might contain @
        # Strategy: split from the right on @ to get host part first
        parts = after_protocol.rsplit("@", 1)
        
        if len(parts) == 2:
            user_pass = parts[0]
            host_db = parts[1]
            
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                
                # URL encode ONLY the password using quote
                # safe='' means encode everything including /
                encoded_password = quote(password, safe='')
                
                # Reconstruct URL
                encoded_url = f"postgresql://{user}:{encoded_password}@{host_db}"
                
                print(f"[ENCODED] Password encoded from {len(password)} to {len(encoded_password)} chars")
                return encoded_url
    
    print("[WARN] Could not parse URL, using as-is")
    return raw_url

def create_tables():
    """Create all tables in Supabase PostgreSQL"""
    
    print("[CONNECTING] Connecting to Supabase...")
    db_url = get_encoded_db_url()
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    try:
        print("[CREATE] Creating ideas table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                title TEXT,
                description TEXT,
                problem_solved TEXT,
                time_estimate TEXT,
                cost_estimate TEXT,
                resources_needed TEXT,
                impact TEXT,
                complexity TEXT,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        print("[CREATE] Creating conversations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id TEXT UNIQUE,
                messages JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("[CREATE] Creating feedback table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                idea_id INTEGER REFERENCES ideas(id),
                human_decision TEXT,
                ai_score FLOAT,
                ai_recommendation TEXT,
                feedback_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        print("[INDEX] Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ideas_session 
            ON ideas(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ideas_status 
            ON ideas(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ideas_domain 
            ON ideas(domain)
        """)
        
        conn.commit()
        print("[SUCCESS] All tables created successfully!")
        
        # Show table info
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"\n[TABLES] Tables in database: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        print("[CLOSE] Connection closed")

def migrate_from_sqlite():
    """Optional: Migrate existing SQLite data to Supabase"""
    
    import sqlite3
    
    if not os.path.exists("ideas.db"):
        print("[INFO] No SQLite database found. Skipping migration.")
        return
    
    print("\n[MIGRATE] Migrating data from SQLite...")
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect("ideas.db")
    sqlite_cursor = sqlite_conn.cursor()
    
    db_url = get_encoded_db_url()
    pg_conn = psycopg2.connect(db_url)
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get all ideas from SQLite
        sqlite_cursor.execute("SELECT * FROM ideas")
        ideas = sqlite_cursor.fetchall()
        
        print(f"[FOUND] Found {len(ideas)} ideas to migrate")
        
        for idea in ideas:
            pg_cursor.execute("""
                INSERT INTO ideas (
                    session_id, title, description, problem_solved,
                    time_estimate, cost_estimate, resources_needed,
                    impact, complexity, domain, created_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, idea[1:])  # Skip id, let PostgreSQL auto-increment
        
        pg_conn.commit()
        print(f"[SUCCESS] Migrated {len(ideas)} ideas successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration error: {e}")
        pg_conn.rollback()
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Supabase Database Setup")
    print("=" * 50)
    
    create_tables()
    migrate_from_sqlite()
    
    print("\n[SUCCESS] Database migration complete!")
    print("[READY] Ready to use Supabase PostgreSQL!")
