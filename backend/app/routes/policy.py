from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_token
from app.models import Policy

router = APIRouter(prefix="/policy", tags=["policy"])


class PolicyCreate(BaseModel):
    name: str
    service: str
    allowed_actions: list[str] = []
    denied_actions: list[str] = []
    require_stepup_above_risk: float = 0.7


@router.get("/")
async def list_policies(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    org_id = token["sub"].split("|")[0] if "|" in token["sub"] else "default"
    result = await db.execute(select(Policy).where(Policy.org_id == org_id, Policy.active == True))
    policies = result.scalars().all()
    return {"policies": [
        {
            "id": p.id,
            "name": p.name,
            "service": p.service,
            "allowed_actions": p.allowed_actions,
            "denied_actions": p.denied_actions,
            "require_stepup_above_risk": p.require_stepup_above_risk,
        }
        for p in policies
    ]}


@router.post("/")
async def create_policy(
    body: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    org_id = token["sub"].split("|")[0] if "|" in token["sub"] else "default"
    policy = Policy(
        org_id=org_id,
        name=body.name,
        service=body.service,
        allowed_actions=body.allowed_actions,
        denied_actions=body.denied_actions,
        require_stepup_above_risk=body.require_stepup_above_risk,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return {"id": policy.id, "name": policy.name}


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token),
):
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.active = False
    await db.commit()
    return {"deleted": True}
