# Garbage Backend

## Setup
1. cp .env.example .env  # Fill keys
2. pip install -r requirements.txt
3. uvicorn app.main:app --reload --port 8001

Swagger: http://localhost:8001/docs