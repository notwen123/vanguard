"""
Step-up authentication via Auth0 MFA.
Triggers a push notification / MFA challenge for high-risk actions.
"""
import httpx
from app.config import settings
from app.auth import get_management_token

async def trigger_stepup(user_sub: str, context: dict) -> dict:
    """
    Enroll user in a step-up MFA challenge via Auth0.
    Returns a challenge_id that the frontend polls to check approval.
    """
    mgmt_token = await get_management_token()

    async with httpx.AsyncClient() as client:
        # Trigger MFA challenge for the user
        resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/mfa/challenge",
            headers={"Authorization": f"Bearer {mgmt_token}"},
            json={
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "challenge_type": "otp oob",
                "mfa_token": context.get("mfa_token", ""),
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            return {
                "challenge_id": data.get("oob_code", data.get("challenge_id")),
                "challenge_type": data.get("challenge_type", "oob"),
                "binding_method": data.get("binding_method"),
            }
        else:
            # Fallback: return a pending challenge that requires dashboard approval
            return {
                "challenge_id": f"pending_{user_sub}_{context.get('request_id', 'unknown')}",
                "challenge_type": "dashboard_approval",
                "binding_method": "prompt",
            }


async def verify_stepup(challenge_id: str, otp_code: str, mfa_token: str) -> bool:
    """Verify the step-up OTP/OOB response."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "http://auth0.com/oauth/grant-type/mfa-oob",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "mfa_token": mfa_token,
                "oob_code": challenge_id,
                "binding_code": otp_code,
            },
        )
        return resp.status_code == 200
