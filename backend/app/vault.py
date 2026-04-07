"""
Local Encrypted Vault — free replacement for Auth0 Token Vault.
Stores service credentials encrypted at rest using Fernet (AES-128-CBC + HMAC).
Agents NEVER see raw tokens — only Vanguard reads from the vault.
"""
import os
import json
from cryptography.fernet import Fernet
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.database import Base

# ---------------------------------------------------------------------------
# Vault DB model
# ---------------------------------------------------------------------------

class VaultSecret(Base):
    __tablename__ = "vault_secrets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_sub: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    key = os.environ.get("VAULT_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("VAULT_ENCRYPTION_KEY not set in environment")
    return Fernet(key.encode())

def encrypt_token(raw_token: str) -> str:
    return _get_fernet().encrypt(raw_token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()

# ---------------------------------------------------------------------------
# Vault operations
# ---------------------------------------------------------------------------

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def store_secret(
    db: AsyncSession,
    user_sub: str,
    service: str,
    raw_token: str,
    scopes: list[str] | None = None,
) -> VaultSecret:
    """Store an encrypted token in the vault."""
    # Remove existing entry for same user+service
    existing = await db.execute(
        select(VaultSecret).where(
            VaultSecret.user_sub == user_sub,
            VaultSecret.service == service,
        )
    )
    old = existing.scalar_one_or_none()
    if old:
        await db.delete(old)

    secret = VaultSecret(
        user_sub=user_sub,
        service=service,
        encrypted_token=encrypt_token(raw_token),
        scopes=json.dumps(scopes or []),
    )
    db.add(secret)
    await db.commit()
    await db.refresh(secret)
    return secret


async def retrieve_secret(
    db: AsyncSession,
    user_sub: str,
    service: str,
) -> str:
    """Retrieve and decrypt a token from the vault. Returns raw token."""
    result = await db.execute(
        select(VaultSecret).where(
            VaultSecret.user_sub == user_sub,
            VaultSecret.service == service,
        )
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise ValueError(f"No stored credential for {service}. Please connect this service first.")
    return decrypt_token(secret.encrypted_token)
