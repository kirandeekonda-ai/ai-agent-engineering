"""
Debug: Print the actual connection string being used
"""
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

raw_url = os.getenv("SUPABASE_DB_URL")
print("="*60)
print("DEBUG: Supabase Connection String")
print("="*60)
print(f"\nRaw from .env:\n{raw_url}")

# Remove quotes
raw_url = raw_url.strip('"').strip("'")
print(f"\nAfter removing quotes:\n{raw_url}")

# Parse it
if raw_url.startswith("postgresql://"):
    after_protocol = raw_url.replace("postgresql://", "")
    parts = after_protocol.rsplit("@", 1)
    
    if len(parts) == 2:
        user_pass = parts[0]
        host_db = parts[1]
        
        print(f"\nUser:Password part: {user_pass[:20]}...")
        print(f"Host:Port/DB part: {host_db}")
        
        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
            encoded_password = quote(password, safe='')
            
            encoded_url = f"postgresql://{user}:{encoded_password}@{host_db}"
            
            print(f"\n{'='*60}")
            print("ENCODED URL:")
            print(f"{'='*60}")
            # Hide password for security
            print(encoded_url.replace(encoded_password, "***HIDDEN***"))
            
            # Show host separately
            print(f"\nHost that will be connected to: {host_db.split(':')[0]}")
            print(f"\nFull encoded URL (for testing):")
            print(encoded_url)
