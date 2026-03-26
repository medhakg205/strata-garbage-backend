from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import create_client
import os
import jwt
from jose import JWTError

security = HTTPBearer()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

async def get_current_user(credentials=Depends(security)):
    try:
        # Verify Supabase JWT
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("SUPABASE_JWT_SECRET"),  # From Supabase > Settings > API
            audience="authenticated",
            algorithms=["HS256"]
        )
        user = supabase.auth.get_user(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.user
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Auth failed")