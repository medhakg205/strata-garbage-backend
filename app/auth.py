a
import os
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Load environment variables ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

security = HTTPBearer()

# --- Initialize Supabase client ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
print(f"❌ AUTH ERROR: Missing Supabase variables in {BASE_DIR / '.env'}")
else:
print("✅ Auth service initialized.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


async def get_current_user(credentials=Depends(security)):
"""
Verifies Supabase token, then fetches the user's role from 'public.users'.
Returns a dict: {id, email, role}
"""
token = credentials.credentials

try:
# 1️⃣ Verify token
auth_resp = supabase.auth.get_user(token)
user = auth_resp.user
if not user:
raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

# 2️⃣ Fetch role from database
resp = supabase.table("users").select("*").eq("id", user.id).single().execute()
db_user = resp.data
if not db_user:
raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found in database")

return {
"id": user.id,
"email": user.email,
"role": db_user["role"] # use the role stored in your users table
}

except Exception as e:
print(f"❌ AUTH ERROR: {str(e)}")
raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}"
