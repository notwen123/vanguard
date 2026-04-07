from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Any
import uuid

from app.database import get_db
from app.auth import verify_token

limiter = Limiter(key_func=get_remote_address)
from app.supervisor import classify_intent
from app.token_vault import get_scoped_token
from app.executor import execute_action
from app.stepup import trigger_stepup, verify_stepup
from app.models import AuditLog, Policy
from sqlalchemy import select
from datetime import datetime, timezone

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    intent: str
    action: str
    service: str
    parameters: dict[str, Any] = {}
    agent_id: str = "default-agent"
    mfa_token: str | None = None  # provided if step-up already completed


class AgentResponse(BaseModel):
    request_id: str
    decision: str
    risk_score: float
    reasoning: str
    result: dict | None = None
    stepup_required: bool = False
    stepup_challenge: dict | None = None
    audit_id: int | None = None


@router.post("/request", response_model=AgentResponse)
@limiter.limit("30/minute")
async def handle_agent_request(
    request: Request,
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    token_payload: dict = Depends(verify_token),
):
    request_id = str(uuid.uuid4())
    user_sub = token_payload["sub"]

    # 1. Supervisor LLM classifies intent
    classification = await classify_intent(
        intent=req.intent,
        action=req.action,
        service=req.service,
        parameters=req.parameters,
    )

    decision = classification["decision"]
    risk_score = classification["risk_score"]
    reasoning = classification["reasoning"]

    # 2. Check org policy overrides
    policy_result = await _check_policy(db, user_sub, req.service, req.action)
    if policy_result == "FORCE_DENY":
        decision = "DENIED"
        reasoning = "Blocked by organization policy"
    elif policy_result == "FORCE_APPROVE" and decision == "ESCALATE":
        decision = "APPROVED"

    # 3. Handle step-up for ESCALATE
    stepup_challenge = None
    if decision == "ESCALATE":
        if req.mfa_token:
            # MFA already completed — treat as approved
            decision = "APPROVED"
        else:
            challenge = await trigger_stepup(
                user_sub=user_sub,
                context={"request_id": request_id},
                db=db,
            )
            # Log and return — execution pending human approval
            audit = await _log_decision(
                db, request_id, req, user_sub, "ESCALATED", risk_score, reasoning, False, None
            )
            return AgentResponse(
                request_id=request_id,
                decision="ESCALATED",
                risk_score=risk_score,
                reasoning=reasoning,
                stepup_required=True,
                stepup_challenge=challenge,
                audit_id=audit.id,
            )

    # 4. Execute if approved
    result = None
    token_issued = False

    if decision == "APPROVED":
        try:
            token_info = await get_scoped_token(user_sub, req.service, req.action, db=db)
            token_issued = True
            result = await execute_action(
                service=req.service,
                action=req.action,
                parameters=req.parameters,
                access_token=token_info["_access_token"],
            )
        except Exception as e:
            decision = "FAILED"
            reasoning = f"Execution error: {str(e)}"

    # 5. Audit log
    audit = await _log_decision(
        db, request_id, req, user_sub, decision, risk_score, reasoning, token_issued, result
    )

    return AgentResponse(
        request_id=request_id,
        decision=decision,
        risk_score=risk_score,
        reasoning=reasoning,
        result=result,
        audit_id=audit.id,
    )


async def _check_policy(db: AsyncSession, user_sub: str, service: str, action: str) -> str | None:
    """Check if org policy forces a decision override."""
    # Use user_sub org prefix as org_id (Auth0 org pattern)
    org_id = user_sub.split("|")[0] if "|" in user_sub else "default"
    result = await db.execute(
        select(Policy).where(
            Policy.org_id == org_id,
            Policy.service == service,
            Policy.active == True,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        return None
    if action in policy.denied_actions:
        return "FORCE_DENY"
    if action in policy.allowed_actions:
        return "FORCE_APPROVE"
    return None


async def _log_decision(
    db, request_id, req, user_sub, decision, risk_score, reasoning, token_issued, result
) -> AuditLog:
    log = AuditLog(
        agent_id=req.agent_id,
        user_sub=user_sub,
        intent=req.intent,
        action=req.action,
        service=req.service,
        decision=decision,
        risk_score=risk_score,
        supervisor_reasoning=reasoning,
        token_issued=token_issued,
        execution_result=str(result) if result else None,
        metadata_json={"request_id": request_id, "parameters_keys": list(req.parameters.keys())},
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
