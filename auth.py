"""
Autenticación username + password con JWT.
Sin servicios externos — todo en el backend.

Variables de entorno:
    JWT_SECRET  — clave secreta (cambiar en prod, default solo para dev)
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException

JWT_SECRET = os.getenv("JWT_SECRET", "gema-med-dev-secret-change-in-production")
JWT_ALGO   = "HS256"
JWT_DAYS   = 30


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Returns 'salt:hash' string."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == h
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_token(user_id: int, username: str, display_name: str = "") -> str:
    payload = {
        "sub":          str(user_id),
        "username":     username,
        "display_name": display_name,
        "exp":          datetime.now(timezone.utc) + timedelta(days=JWT_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


# ── FastAPI Dependencies ──────────────────────────────────────────────────────

async def get_current_user(authorization: str = Header(default=None)) -> dict:
    """
    Requiere JWT válido. Retorna {user_id, username, display_name}.
    Lanza 401 si falta o es inválido.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization: Bearer <token> requerido")
    token = authorization[7:]
    try:
        p = _decode_token(token)
        return {
            "user_id":      p["sub"],
            "username":     p.get("username", ""),
            "display_name": p.get("display_name", ""),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado — inicia sesión de nuevo")
    except Exception as e:
        raise HTTPException(401, f"Token inválido: {e}")


async def get_optional_user(authorization: str = Header(default=None)) -> dict:
    """
    Auth opcional — para endpoints usados también por Telegram / dev.
    Si no hay token, retorna user_id='dev_user'.
    """
    if not authorization:
        return {"user_id": "dev_user", "username": "dev", "display_name": "Developer"}
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return {"user_id": "dev_user", "username": "dev", "display_name": "Developer"}
