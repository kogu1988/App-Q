"""Auth router — JWT tabanlı kayıt ve giriş (enterprise auth).

`/api/auth/register` parola ile kayıt eder + access token döndürür.
`/api/auth/login` parolayı doğrular + access token döndürür.

Not: Mevcut `X-Username` header akışı geriye dönük uyumluluk için korunur;
JWT doğrulamasını middleware'e bağlamak bir sonraki adımdır.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.research_engine.auth_utils import hash_password, verify_password
from packages.research_engine.database import (
    get_client_by_username,
    get_client_password_hash,
    register_client_if_new,
    set_client_password,
)
from packages.research_engine.jwt_utils import create_token

router = APIRouter()


class AuthRegister(BaseModel):
    username: str
    password: str
    email: str = ""


class AuthLogin(BaseModel):
    username: str
    password: str


def _validate_username(username: str) -> str:
    username = (username or "").strip()
    if not username or len(username) < 2 or len(username) > 20:
        raise HTTPException(status_code=400, detail="Kullanıcı adı 2-20 karakter arasında olmalı.")
    if not username.isalnum() and not all(c.isalnum() or c in "-_" for c in username):
        raise HTTPException(status_code=400, detail="Kullanıcı adı sadece harf, rakam, - ve _ içerebilir.")
    return username


@router.post("/register")
async def register(req: AuthRegister):
    username = _validate_username(req.username)
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Parola en az 6 karakter olmalı.")

    client, created = register_client_if_new(username, req.email)
    set_client_password(username, hash_password(req.password))
    token = create_token(username)

    return {
        "username": username,
        "plan_type": client.get("plan_type", "Free"),
        "created": created,
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login")
async def login(req: AuthLogin):
    username = (req.username or "").strip()
    stored = get_client_password_hash(username)
    if not stored or not verify_password(req.password, stored):
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya parola.")

    client = get_client_by_username(username) or {}
    token = create_token(username)

    return {
        "username": username,
        "plan_type": client.get("plan_type", "Free"),
        "access_token": token,
        "token_type": "bearer",
    }
