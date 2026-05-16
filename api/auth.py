import os
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter()
_bearer = HTTPBearer()
_SECRET = os.getenv("JWT_SECRET", "change-me-in-env")
_MOD_PW = os.getenv("MOD_PASSWORD", "")


class LoginBody(BaseModel):
    password: str


@router.post("/login")
def login(body: LoginBody):
    if not _MOD_PW or body.password != _MOD_PW:
        raise HTTPException(401, "Wrong password")
    token = jwt.encode(
        {"role": "moderator", "exp": datetime.utcnow() + timedelta(hours=8)},
        _SECRET,
        algorithm="HS256",
    )
    return {"token": token}


def require_mod(creds: HTTPAuthorizationCredentials = Depends(_bearer)):
    try:
        payload = jwt.decode(creds.credentials, _SECRET, algorithms=["HS256"])
        if payload.get("role") != "moderator":
            raise HTTPException(403, "Forbidden")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
