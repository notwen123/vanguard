"""
Auth0 Token Vault integration.
Retrieves scoped tokens for approved agent actions.
Agents NEVER see raw credentials — only Vanguard touches the vault.
"""
import httpx
from app.config import settings
from app.auth import get_management_token

# Map service+action to minimal required scopes
SCOPE_MAP = {
    "slack": {
        "send_message": ["chat:write"],
        "read_channel": ["channels:read", "channels:history"],
        "list_users": ["users:read"],
        "create_channel": ["channels:manage"],
        "delete_channel": ["channels:manage", "channels:write"],
    },
    "github": {
        "create_issue": ["repo"],
        "read_repo": ["repo:status", "public_repo"],
        "create_pr": ["repo"],
        "delete_repo": ["delete_repo"],
        "push_code": ["repo"],
    },
    "gmail": {
        "send_email": ["https://www.googleapis.com/auth/gmail.send"],
        "read_email": ["https://www.googleapis.com/auth/gmail.readonly"],
    },
}

async def get_scoped_token(
    user_sub: str,
    service: str,
    action: str,
) -> dict:
    """
    Exchange for a scoped token from Auth0 Token Vault.
    Returns token info without exposing the raw secret to the agent.
    """
    scopes = SCOPE_MAP.get(service, {}).get(action, [])
    if not scopes:
        raise ValueError(f"No scope mapping for {service}/{action}")

    mgmt_token = await get_management_token()

    # Token Vault API: retrieve the stored token for this user+service
    async with httpx.AsyncClient() as client:
        # Get the token vault connection for this user
        resp = await client.get(
            f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_sub}/credentials",
            headers={"Authorization": f"Bearer {mgmt_token}"},
        )
        resp.raise_for_status()
        credentials = resp.json()

        # Find the credential for the requested service
        service_cred = next(
            (c for c in credentials if service.lower() in c.get("name", "").lower()),
            None,
        )
        if not service_cred:
            raise ValueError(f"No stored credential found for service: {service}")

        # Exchange for a scoped access token via Token Vault
        token_resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_sub}/credentials/{service_cred['id']}/token",
            headers={"Authorization": f"Bearer {mgmt_token}"},
            json={"scopes": scopes},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

    return {
        "service": service,
        "action": action,
        "scopes_granted": scopes,
        "token_type": token_data.get("token_type", "Bearer"),
        # We return the access token only for internal execution — never forwarded to agent
        "_access_token": token_data.get("access_token"),
    }
