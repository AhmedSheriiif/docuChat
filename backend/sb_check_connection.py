"""
Step 1 test: prove we can connect to Supabase and that the schema we created
in the SQL editor (documents, chunks, match_chunks) actually exists.

Run from the backend/ folder:
    python test_connection.py

This script does NOT touch embeddings, chunking, or Groq. Its only job is to
answer one question: "is the database reachable and shaped correctly?"
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load backend/.env
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def main():
    print("1. Checking .env values are present...")
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("   FAILED: SUPABASE_URL or SUPABASE_SERVICE_KEY is empty.")
        print("   -> Copy .env.example to .env and fill in your real values.")
        return
    print(f"   OK. URL = {SUPABASE_URL}")

    print("\n2. Connecting to Supabase...")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("   OK. Client created.")
    except Exception as e:
        print(f"   FAILED to create client: {e}")
        return

    print("\n3. Checking the 'documents' table exists and is reachable...")
    try:
        result = client.table("documents").select("id").limit(1).execute()
        print(f"   OK. Table reachable. Rows found so far: {len(result.data)}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   -> Did the CREATE TABLE documents... SQL run successfully?")
        return

    print("\n4. Checking the 'chunks' table exists and is reachable...")
    try:
        result = client.table("chunks").select("id").limit(1).execute()
        print(f"   OK. Table reachable. Rows found so far: {len(result.data)}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   -> Did the CREATE TABLE chunks... SQL run successfully?")
        return

    print("\n5. Checking the match_chunks() function exists and is callable...")
    try:
        # Call it with a dummy all-zero 384-dim vector just to prove the
        # function exists and accepts calls. Real vectors come in Step 2.
        dummy_vector = [0.0] * 384
        result = client.rpc(
            "match_chunks",
            {"query_embedding": dummy_vector, "match_count": 1},
        ).execute()
        print(f"   OK. Function is callable. Returned {len(result.data)} row(s).")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   -> Did the CREATE FUNCTION match_chunks... SQL run successfully?")
        return

    print("\nALL CHECKS PASSED. Database is reachable and correctly shaped.")
    print("Ready for Step 2: writing real data into it.")


if __name__ == "__main__":
    main()