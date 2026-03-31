import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # service role key


if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing Supabase auth env variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_current_user(credentials=Depends(security)):
    token = credentials.credentials

    try:
        auth_resp = supabase.auth.get_user(token)
        user = auth_resp.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        resp = supabase.table("users") \
            .select("*") \
            .eq("id", user.id) \
            .single() \
            .execute()

        db_user = resp.data

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found"
            )

        return {
            "id": user.id,
            "email": user.email,
            "role": db_user["role"]
        }

    except Exception as e:
        print("AUTH ERROR:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
