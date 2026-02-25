"""
Migration: Add market research columns to ideas table
Run this once to add the new columns
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import quote

load_dotenv()

def get_encoded_db_url():
    """Get properly URL-encoded database connection string"""
    raw_url = os.getenv("SUPABASE_DB_URL")
    
    if not raw_url:
        raise ValueError("SUPABASE_DB_URL not found in environment variables")
    
    raw_url = raw_url.strip('"').strip("'")
    
    if "%40" in raw_url or "%2A" in raw_url:
        return raw_url
    
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


def run_migration():
    """Add market research columns to ideas table"""
    db_url = get_encoded_db_url()
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Columns to add with their types
    new_columns = [
        ("market_alternatives", "TEXT"),  # JSON array of alternatives
        ("market_maturity", "TEXT"),      # STABLE, EVOLVING, FAST, TRENDING
        ("market_summary", "TEXT"),       # Brief market context
        ("market_recommendation", "TEXT"), # proceed, research_more, consider_existing
        ("research_sources", "TEXT"),     # JSON array of source URLs
    ]
    
    for column_name, column_type in new_columns:
        try:
            cursor.execute(f"""
                ALTER TABLE ideas 
                ADD COLUMN IF NOT EXISTS {column_name} {column_type}
            """)
            print(f"[OK] Added column: {column_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"[SKIP] Column {column_name} already exists")
            else:
                print(f"[ERROR] Error adding {column_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n[OK] Migration complete!")


if __name__ == "__main__":
    print("Running migration: Add market research columns...")
    run_migration()
