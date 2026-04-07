"""
Token Vault — Auth0 Token Vault (REQUIRED for hackathon judging).
Falls back to local encrypted vault when AUTH_MODE=local (dev/demo).

Auth0 Token Vault is FREE on the dev tenant — no paid plan needed.
Sign up at: auth0.com/signup
"""
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.vault import retrieve_secret

# Minimal scopes per service+action
SCOPE_MAP = {
    "slack": {
        "send_message": ["chat:write"],
        "read_channel": ["channels:read", "channels:history"],
        "list_users": ["users:read"],
        "create_channel": ["channels:manage"],
        "delete_channel": ["channels:manage"],
    },
    "github": {
        "create_issue": ["repo"],
        "read_repo": ["repo:status", "public_repo"],
        "create_pr": ["repo"],
        "push_code": ["repo"],
        "delete_repo": ["delete_repo"],
    },
    "gmail": {
        "send_email": ["https://www.googleapis.com/auth/gmail.send"],
        "read_email": ["https://www.googleapis.com/auth/gmail.readonly"],
    },
}


async def _get_mgmt_token() -> str:
    """Get Auth0 Management API token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "audience": f"https://{settings.AUTH0_DOMAIN}/api/v2/",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def _get_token_from_auth0_vault(user_sub: str, service: str, action: str) -> str:
    """
    Retrieve a scoped token from Auth0 Token Vault.
    This is the real implementation — required for hackathon.
    """
    scopes = SCOPE_MAP.get(service, {}).get(action, [])
    mgmt_token = await _get_mgmt_token()

    async with httpx.AsyncClient() as client:
        # List user credentials from Token Vault
        resp = await client.get(
            f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_sub}/credentials",
            headers={"Authorization": f"Bearer {mgmt_token}"},
        )
        resp.raise_for_status()
        credentials = resp.json()

        # Find credential for the requested service
        cred = next(
            (c for c in credentials if service.lower() in c.get("name", "").lower()),
            None,
        )
        if not cred:
            raise ValueError(
                f"No Auth0 Token Vault credential found for '{service}'. "
                f"Please connect this service via the dashboard first."
            )

        # Exchange for scoped access token via Token Vault
        token_resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_sub}/credentials/{cred['id']}/token",
            headers={"Authorization": f"Bearer {mgmt_token}"},
            json={"scopes": scopes},
        )
        token_resp.raise_for_status()
        return token_resp.json()["access_token"]


async def get_scoped_token(
    user_sub: str,
    service: str,
    action: str,
    db: AsyncSession = None,
) -> dict:
    """
    Get a scoped token for the requested service+action.
    - AUTH_MODE=auth0 → uses Auth0 Token Vault (required for hackathon judging)
    - AUTH_MODE=local → uses local encrypted vault (dev/demo without Auth0)
    Agents NEVER receive the raw token — only Vanguard uses it internally.
    """
    import os
    scopes = SCOPE_MAP.get(service, {}).get(action)
    if scopes is None:
        raise ValueError(f"No scope mapping for {service}/{action}")

    mode = os.environ.get("AUTH_MODE", "auth0").lower()

    if mode == "auth0":
        raw_token = await _get_token_from_auth0_vault(user_sub, service, action)
    else:
        # Local fallback — uses Fernet-encrypted SQLite vault
        raw_token = await retrieve_secret(db, user_sub, service)

    return {
        "service": service,
        "action": action,
        "scopes_granted": scopes,
        "token_type": "Bearer",
        "_access_token": raw_token,  # internal only — never forwarded to agent
    }
