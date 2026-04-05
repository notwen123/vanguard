from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.database import get_db
from app.auth import verify_token
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    service: str | None = None,
    decision: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_token),
):
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    if service:
        query = query.where(AuditLog.service == service)
    if decision:
        query = query.where(AuditLog.decision == decision)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "agent_id": log.agent_id,
                "intent": log.intent,
                "action": log.action,
                "service": log.service,
                "decision": log.decision,
                "risk_score": log.risk_score,
                "reasoning": log.supervisor_reasoning,
                "token_issued": log.token_issued,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_token),
):
    total = await db.execute(select(func.count(AuditLog.id)))
    approved = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.decision == "APPROVED"))
    denied = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.decision == "DENIED"))
    escalated = await db.execute(select(func.count(AuditLog.id)).where(AuditLog.decision == "ESCALATED"))
    avg_risk = await db.execute(select(func.avg(AuditLog.risk_score)))

    return {
        "total_requests": total.scalar(),
        "approved": approved.scalar(),
        "denied": denied.scalar(),
        "escalated": escalated.scalar(),
        "avg_risk_score": round(avg_risk.scalar() or 0, 3),
    }
