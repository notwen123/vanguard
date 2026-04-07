"""
Step-up authentication — FREE implementation using TOTP (RFC 6238).
Compatible with Google Authenticator, Authy, any TOTP app.
No paid Auth0 plan required.
"""
import pyotp
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.database import Base


class TotpSecret(Base):
    __tablename__ = "totp_secrets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_sub: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    secret: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


async def get_or_create_totp(db: AsyncSession, user_sub: str) -> str:
    """Get existing TOTP secret or create one for this user."""
    result = await db.execute(select(TotpSecret).where(TotpSecret.user_sub == user_sub))
    row = result.scalar_one_or_none()
    if row:
        return row.secret
    secret = pyotp.random_base32()
    db.add(TotpSecret(user_sub=user_sub, secret=secret))
    await db.commit()
    return secret


async def trigger_stepup(user_sub: str, context: dict, db: AsyncSession = None) -> dict:
    """
    Returns a TOTP provisioning URI so the user can scan it with
    Google Authenticator / Authy. On subsequent calls returns the issuer info.
    """
    secret = await get_or_create_totp(db, user_sub)
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user_sub, issuer_name="Vanguard Gateway")
    return {
        "challenge_type": "totp",
        "provisioning_uri": uri,   # scan this QR code once
        "issuer": "Vanguard Gateway",
        "request_id": context.get("request_id"),
        "instructions": "Enter the 6-digit code from your authenticator app",
    }


async def verify_stepup(user_sub: str, otp_code: str, db: AsyncSession) -> bool:
    """Verify a TOTP code. Returns True if valid."""
    result = await db.execute(select(TotpSecret).where(TotpSecret.user_sub == user_sub))
    row = result.scalar_one_or_none()
    if not row:
        return False
    totp = pyotp.TOTP(row.secret)
    return totp.verify(otp_code, valid_window=1)  # ±30s tolerance
