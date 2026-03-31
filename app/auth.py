import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service role key
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_JWT_SECRET:
    raise Exception("Missing Supabase auth env variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        # ✅ VERIFY JWT LOCALLY (CORRECT WAY)
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # ✅ FETCH USER FROM DB (UNCHANGED LOGIC)
        resp = supabase.table("users") \
            .select("*") \
            .eq("id", user_id) \
            .single() \
            .execute()

        db_user = resp.data

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )

        return {
            "id": user_id,
            "email": email,
            "role": db_user["role"]
        }

    except Exception as e:
        print("AUTH ERROR:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
