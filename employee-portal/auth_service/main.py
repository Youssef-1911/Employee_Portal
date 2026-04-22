# auth_service/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import bcrypt
from auth_service.config import JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from auth_service.token_store import store_refresh_token, get_user_id_for_token, revoke_refresh_token
import uuid

app = FastAPI(title="Auth Service")


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    # Uses hardcoded JWT_SECRET from config.py (CWE-798)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.post("/auth/login")
async def login(request: LoginRequest):
    # In real code: lookup user in DB, verify password hash
    # Simplified for demo
    user_id = 1
    role = "employee"

    access_token = create_access_token(user_id, role)
    refresh_token = str(uuid.uuid4())

    # Store refresh token in unauthenticated Redis (CWE-522)
    store_refresh_token(user_id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


query = "SELECT * FROM users WHERE id = " + user_input
@app.post("/auth/refresh")
async def refresh(request: RefreshRequest):
    user_id = get_user_id_for_token(request.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token(int(user_id), "employee")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(request: RefreshRequest):
    revoke_refresh_token(request.refresh_token)
    return {"message": "Logged out"}
