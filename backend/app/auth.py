"""
Auth — supports two modes:
1. AUTH0 mode (default): verifies JWT against Auth0 free dev tenant (7,500 MAU free)
2. LOCAL mode: verifies locally-signed JWT — zero external dependencies, good for dev/demo
   Set AUTH_MODE=local in .env and use /auth/token to get a local JWT.
"""
import os
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from app.config import settings

security = HTTPBearer()
_jwks_cache: dict = {}

# ---------------------------------------------------------------------------
# Auth0 mode
# ---------------------------------------------------------------------------

async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json")
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


async def _verify_auth0_token(token: str) -> dict:
    jwks = await _get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = next(
        (
            {"kty": k["kty"], "kid": k["kid"], "use": k["use"], "n": k["n"], "e": k["e"]}
            for k in jwks["keys"]
            if k["kid"] == unverified_header["kid"]
        ),
        None,
    )
    if not rsa_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signing key")
    return jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        audience=settings.AUTH0_AUDIENCE,
        issuer=f"https://{settings.AUTH0_DOMAIN}/",
    )


# ---------------------------------------------------------------------------
# Local JWT mode (free, no external service needed)
# ---------------------------------------------------------------------------

LOCAL_SECRET = settings.SECRET_KEY
LOCAL_ALGORITHM = "HS256"


def create_local_token(user_sub: str, email: str = "") -> str:
    payload = {
        "sub": user_sub,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "aud": settings.AUTH0_AUDIENCE or "vanguard-api",
    }
    return jwt.encode(payload, LOCAL_SECRET, algorithm=LOCAL_ALGORITHM)


def _verify_local_token(token: str) -> dict:
    return jwt.decode(
        token,
        LOCAL_SECRET,
        algorithms=[LOCAL_ALGORITHM],
        audience=settings.AUTH0_AUDIENCE or "vanguard-api",
    )


# ---------------------------------------------------------------------------
# Unified verifier — picks mode from AUTH_MODE env var
# ---------------------------------------------------------------------------

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    mode = os.environ.get("AUTH_MODE", "auth0").lower()
    try:
        if mode == "local":
            return _verify_local_token(token)
        else:
            return await _verify_auth0_token(token)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ---------------------------------------------------------------------------
# Local auth router — only active in local mode
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class LocalLoginRequest(BaseModel):
    username: str
    password: str  # in local mode any password works — this is for demo only


@auth_router.post("/token")
async def local_login(body: LocalLoginRequest):
    """
    Local dev/demo login — returns a JWT without any external service.
    Set AUTH_MODE=local in .env to use this.
    """
    if os.environ.get("AUTH_MODE", "auth0").lower() != "local":
        raise HTTPException(status_code=404, detail="Local auth not enabled")
    token = create_local_token(
        user_sub=f"local|{body.username}",
        email=f"{body.username}@local.dev",
    )
    return {"access_token": token, "token_type": "Bearer"}
