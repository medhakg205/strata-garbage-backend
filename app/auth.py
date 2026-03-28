import os
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import create_client, Client
from dotenv import load_dotenv

# --- DYNAMIC ENV LOADING ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

security = HTTPBearer()

# --- INITIALIZE SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Check if variables loaded
if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
    print(f"❌ AUTH ERROR: Missing variables in {BASE_DIR / '.env'}")
else:
    print("✅ Auth service (SDK Mode) initialized.")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

async def get_current_user(credentials=Depends(security)):
    """
    Asks Supabase to verify the token. 
    This bypasses 'Algorithm Mismatch' and 'Malformed PEM' errors 
    because the SDK handles the crypto logic internally.
    """
    token = credentials.credentials
    
    try:
        # 1. Ask Supabase to fetch the user associated with this token
        # This verify's the token's validity, expiration, and signature automatically.
        auth_resp = supabase.auth.get_user(token)
        
        # In the Supabase Python SDK, the user object is in .user
        user = auth_resp.user
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # 2. Extract metadata (Role)
        # Supabase stores custom roles in app_metadata
        app_metadata = getattr(user, "app_metadata", {})
        role = app_metadata.get("role", "authenticated")

        # 3. Return a dict that matches your 'main.py' usage: current_user["id"]
        return {
            "id": user.id, 
            "role": role,
            "email": user.email
        }

    except Exception as e:
        # If the token is fake or expired, Supabase will throw an error here
        print(f"❌ AUTH ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )