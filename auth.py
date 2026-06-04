"""
Clerk JWT verification for GEMA-MED FastAPI backend.

Dev mode  (CLERK_DOMAIN not set): auth is skipped, returns "dev_user".
Prod mode (CLERK_DOMAIN set):     verifies Clerk JWT via JWKS.

Add to .env:
    CLERK_DOMAIN=your-app.clerk.accounts.dev   ← from Clerk dashboard → API Keys
"""

import os
from functools import lru_cache
from fastapi import Header, HTTPException

CLERK_DOMAIN = os.getenv("CLERK_DOMAIN", "")


@lru_cache(maxsize=1)
def _jwks_client():
    """Cache the JWKS client (fetches public keys from Clerk once at startup)."""
    if not CLERK_DOMAIN:
        return None
    try:
        from jwt import PyJWKClient
        return PyJWKClient(f"https://{CLERK_DOMAIN}/.well-known/jwks.json")
    except Exception as e:
        print(f"Warning: could not init JWKS client: {e}")
        return None


async def get_current_user(authorization: str = Header(default=None)) -> str:
    """
    FastAPI dependency — resolves to a user identifier string.

    - Dev  (no CLERK_DOMAIN): returns "dev_user" with no token required.
    - Prod (CLERK_DOMAIN set): extracts and verifies Clerk JWT, returns Clerk user_id.
    """
    client = _jwks_client()

    if client is None:
        # Dev bypass — usable without token
        return "dev_user"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization: Bearer <token> required")

    token = authorization[7:]
    try:
        import jwt
        key     = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, key.key, algorithms=["RS256"])
        return payload["sub"]  # Clerk user_id, e.g. "user_2abc..."
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
