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
    Verifies Supabase JWT token, fetches user from public.users table.
    Returns: {id, email, role} - only for 'collector'/'admin' roles.
    Raises 401/403 for invalid/unauthorized users.
    """
    token = credentials.credentials

    try:
        # 1️⃣ Verify JWT token with Supabase Auth
        auth_resp = supabase.auth.get_user(token)
        if not auth_resp.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token"
            )
        
        user_id = auth_resp.user.id

        # 2️⃣ Fetch profile from YOUR public.users table
        resp = supabase.table("users") \
            .select("id, email, role") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        db_user = resp.data
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User profile not found"
            )

        # 3️⃣ Enforce collector/admin role for protected routes
        if db_user["role"] not in ["collector", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Collector or Admin access required"
            )

        # ✅ Return verified user data
        return {
            "id": db_user["id"],
            "email": db_user["email"],
            "role": db_user["role"]
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ AUTH ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication failed"
        )
