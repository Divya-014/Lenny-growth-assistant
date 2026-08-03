import os
import sys
from dotenv import load_dotenv

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from supabase import create_client
from supabase._sync.client import SupabaseException

def test_supabase_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY is missing from environment variables.")
        return

    print("Checking connection settings...")
    print(f"URL: {url}")
    print(f"Key preview: {key[:15]}...")

    # 1. Initialize Client
    try:
        client = create_client(url, key)
        print("✅ Client initialization: SUCCESS")
    except SupabaseException as se:
        print(f"❌ Client initialization failed (Regex check): {se}")
        return
    except Exception as e:
        print(f"❌ Client initialization failed (Unexpected error): {e}")
        return

    # 2. Test actual connection by querying database
    try:
        print("\nSending test query to Supabase (fetching 'chat_sessions')...")
        # Attempt to select a single record from chat_sessions
        response = client.table("chat_sessions").select("id").limit(1).execute()
        print("✅ Database Connection: SUCCESS!")
        print(f"   Successfully communicated with Supabase. Query response data: {response.data}")
    except Exception as e:
        print("❌ Connection/Database check failed!")
        print("\nPossible reasons:")
        print("1. Your API key might be invalid (unauthorized).")
        print("2. The table 'chat_sessions' does not exist in your database yet.")
        print("3. Row-Level Security (RLS) policies might be blocking the select query.")
        print(f"\nExact error traceback:\n{e}")

if __name__ == "__main__":
    test_supabase_connection()
