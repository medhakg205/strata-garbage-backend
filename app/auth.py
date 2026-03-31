import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv
from jose import jwt, JWTError

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
        # 🔍 DEBUG (keep for now)
        print("TOKEN RECEIVED:", token)

        # ✅ VERIFY JWT (removed strict audience to avoid mismatch issues)
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"]
        )

        print("DECODED PAYLOAD:", payload)

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # ✅ FETCH USER FROM DB (unchanged logic)
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

    except JWTError as e:
        print("JWT ERROR:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    except Exception as e:
        print("AUTH ERROR:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
