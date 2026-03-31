# auth.py
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# 🔐 HTTP Bearer security scheme
security = HTTPBearer()

# 🔑 Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # MUST be service role key

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing Supabase environment variables: SUPABASE_URL or SUPABASE_KEY")

# ⚡ Initialize Supabase client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the bearer token from frontend against Supabase and fetches user info from DB.
    Works with ES256 access tokens (default for Supabase auth sessions).
    """
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing"
        )

    try:
        # ✅ Validate token via Supabase auth API (service role key required)
        auth_resp = supabase.auth.get_user(token)
        user = auth_resp.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # ✅ Lookup user in DB
        db_resp = supabase.table("users") \
            .select("*") \
            .eq("id", user.id) \
            .single() \
            .execute()

        db_user = db_resp.data

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )

        # ✅ Return standardized user object
        return {
            "id": user.id,
            "email": user.email,
            "role": db_user.get("role", "user")  # fallback role
        }

    except Exception as e:
        print("AUTH ERROR:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
