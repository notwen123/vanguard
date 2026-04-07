"""
Secrets management — store/list/delete service tokens in the local encrypted vault.
Users connect their Slack/GitHub/Gmail tokens here once.
Vanguard uses them on their behalf — agents never see raw tokens.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.auth import verify_token
from app.vault import store_secret, VaultSecret
from app.stepup import trigger_stepup, verify_stepup

router = APIRouter(prefix="/secrets", tags=["secrets"])


class StoreSecretRequest(BaseModel):
    service: str   # slack | github | gmail
    token: str     # the raw API token / OAuth access token
    scopes: list[str] = []


class VerifyTotpRequest(BaseModel):
    otp_code: str


@router.post("/store")
async def store_service_token(
    body: StoreSecretRequest,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    """Store an encrypted service token in the vault."""
    user_sub = token["sub"]
    await store_secret(db, user_sub, body.service, body.token, body.scopes)
    return {"stored": True, "service": body.service}


@router.get("/list")
async def list_stored_services(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    """List which services have stored tokens (never returns raw tokens)."""
    user_sub = token["sub"]
    result = await db.execute(
        select(VaultSecret.service, VaultSecret.created_at).where(
            VaultSecret.user_sub == user_sub
        )
    )
    rows = result.all()
    return {
        "connected_services": [
            {"service": r.service, "connected_at": r.created_at.isoformat()}
            for r in rows
        ]
    }


@router.delete("/{service}")
async def delete_service_token(
    service: str,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    """Remove a stored token from the vault."""
    user_sub = token["sub"]
    result = await db.execute(
        select(VaultSecret).where(
            VaultSecret.user_sub == user_sub,
            VaultSecret.service == service,
        )
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="No stored token for this service")
    await db.delete(secret)
    await db.commit()
    return {"deleted": True, "service": service}


@router.get("/totp/setup")
async def get_totp_setup(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    """Get TOTP provisioning URI — scan with Google Authenticator / Authy."""
    user_sub = token["sub"]
    challenge = await trigger_stepup(user_sub=user_sub, context={}, db=db)
    return challenge


@router.post("/totp/verify")
async def verify_totp(
    body: VerifyTotpRequest,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    """Verify a TOTP code for step-up auth."""
    user_sub = token["sub"]
    valid = await verify_stepup(user_sub=user_sub, otp_code=body.otp_code, db=db)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP code")
    return {"verified": True}
