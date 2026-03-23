from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models import Customer, Opportunity, PipelineStage, Proposal

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    total_customers = db.scalar(select(func.count(Customer.id))) or 0
    total_opportunities = db.scalar(select(func.count(Opportunity.id))) or 0
    total_proposals = db.scalar(select(func.count(Proposal.id))) or 0
    total_pipeline = (
        db.scalar(select(func.coalesce(func.sum(Opportunity.estimated_value), 0))) or 0
    )

    stages = db.execute(
        select(PipelineStage).order_by(PipelineStage.position)
    ).scalars().all()

    stage_rows = []
    for stage in stages:
        qty = (
            db.scalar(
                select(func.count(Opportunity.id)).where(Opportunity.stage_id == stage.id)
            )
            or 0
        )
        percent = round((qty / total_opportunities) * 100, 1) if total_opportunities else 0

        stage_rows.append(
            {
                "name": stage.name,
                "qty": qty,
                "color": stage.color or "secondary",
                "percent": percent,
            }
        )

    recent_opportunities = db.execute(
        select(Opportunity)
        .options(
            selectinload(Opportunity.customer),
            selectinload(Opportunity.stage),
            selectinload(Opportunity.owner),
        )
        .order_by(Opportunity.created_at.desc(), Opportunity.id.desc())
        .limit(5)
    ).scalars().all()

    recent_proposals = db.execute(
        select(Proposal)
        .options(
            selectinload(Proposal.customer),
            selectinload(Proposal.owner),
        )
        .order_by(Proposal.created_at.desc(), Proposal.id.desc())
        .limit(5)
    ).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "total_customers": total_customers,
            "total_opportunities": total_opportunities,
            "total_proposals": total_proposals,
            "total_pipeline": float(total_pipeline),
            "stage_rows": stage_rows,
            "recent_opportunities": recent_opportunities,
            "recent_proposals": recent_proposals,
        },
    )