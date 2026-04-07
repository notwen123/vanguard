"""
OAuth connection flow — lets users connect Slack/GitHub/Gmail via Auth0 Token Vault.
This is the "User Consent & Setup" step from the demo workflow.
In local mode, users paste tokens directly. In auth0 mode, OAuth flow stores to Token Vault.
"""
import os
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.config import settings
from app.vault import store_secret

router = APIRouter(prefix="/connect", tags=["connect"])

# OAuth config per service
OAUTH_CONFIG = {
    "slack": {
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": "chat:write,channels:read,channels:history,users:read",
        "client_id_env": "SLACK_CLIENT_ID",
        "client_secret_env": "SLACK_CLIENT_SECRET",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scopes": "repo,issues:write",
        "client_id_env": "GITHUB_CLIENT_ID",
        "client_secret_env": "GITHUB_CLIENT_SECRET",
    },
}


@router.get("/{service}/start")
async def start_oauth(
    service: str,
    request: Request,
    token: dict = Depends(verify_token),
):
    """Redirect user to OAuth provider to connect their account."""
    if service not in OAUTH_CONFIG:
        return {"error": f"Unsupported service: {service}"}

    cfg = OAUTH_CONFIG[service]
    client_id = os.environ.get(cfg["client_id_env"], "")
    if not client_id:
        return {"error": f"{cfg['client_id_env']} not configured"}

    base_url = os.environ.get("NEXT_PUBLIC_BASE_URL", "http://localhost:3000")
    redirect_uri = f"{base_url}/api/connect/{service}/callback"

    # Store user_sub in state so we can associate the token after callback
    state = token["sub"].replace("|", "_")

    params = {
        "client_id": client_id,
        "scope": cfg["scopes"],
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
    }
    url = cfg["auth_url"] + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url)


@router.get("/{service}/callback")
async def oauth_callback(
    service: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback — exchange code for token and store in vault."""
    if service not in OAUTH_CONFIG:
        return {"error": f"Unsupported service: {service}"}

    cfg = OAUTH_CONFIG[service]
    client_id = os.environ.get(cfg["client_id_env"], "")
    client_secret = os.environ.get(cfg["client_secret_env"], "")
    base_url = os.environ.get("NEXT_PUBLIC_BASE_URL", "http://localhost:3000")
    redirect_uri = f"{base_url}/api/connect/{service}/callback"

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            cfg["token_url"],
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        data = resp.json()

    access_token = data.get("access_token") or data.get("authed_user", {}).get("access_token")
    if not access_token:
        return {"error": "Failed to get access token", "detail": data}

    # Restore user_sub from state
    user_sub = state.replace("_", "|", 1)

    # Store in local vault (or Auth0 Token Vault in auth0 mode)
    auth_mode = os.environ.get("AUTH_MODE", "local").lower()
    if auth_mode == "auth0":
        # Store via Auth0 Token Vault Management API
        await _store_in_auth0_vault(user_sub, service, access_token)
    else:
        await store_secret(db, user_sub, service, access_token)

    # Redirect back to dashboard
    return RedirectResponse(f"{base_url}/dashboard?connected={service}")


async def _store_in_auth0_vault(user_sub: str, service: str, access_token: str):
    """Store token in Auth0 Token Vault via Management API."""
    async with httpx.AsyncClient() as client:
        # Get management token
        mgmt_resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "audience": f"https://{settings.AUTH0_DOMAIN}/api/v2/",
            },
        )
        mgmt_token = mgmt_resp.json()["access_token"]

        # Store credential in Token Vault
        await client.post(
            f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_sub}/credentials",
            headers={"Authorization": f"Bearer {mgmt_token}"},
            json={
                "credential_type": "access_token",
                "name": f"{service}-token",
                "token": access_token,
            },
        )
