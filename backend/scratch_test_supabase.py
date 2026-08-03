import os
import sys
from dotenv import load_dotenv

# Add parent dir to path so app can be imported
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key length: {len(key) if key else 0}")
print(f"Key preview: {key[:15]}..." if key else "None")

try:
    client = create_client(url, key)
    print("Successfully created client!")
except Exception as e:
    import traceback
    print("Failed to initialize Supabase client:")
    traceback.print_exc()
