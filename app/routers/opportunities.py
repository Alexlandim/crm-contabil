from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import get_current_user
from app.models import Opportunity, Customer, PipelineStage, User
from app.audit import register_audit

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/", response_class=HTMLResponse)
def list_opportunities(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    opportunities = db.execute(select(Opportunity).order_by(Opportunity.id.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "opportunities/list.html",
        {"request": request, "user": user, "opportunities": opportunities},
    )


@router.get("/new", response_class=HTMLResponse)
def new_opportunity(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    customers = db.execute(select(Customer).order_by(Customer.legal_name)).scalars().all()
    stages = db.execute(select(PipelineStage).order_by(PipelineStage.position)).scalars().all()
    users = db.execute(select(User).order_by(User.full_name)).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "opportunities/form.html",
        {
            "request": request,
            "user": user,
            "customers": customers,
            "stages": stages,
            "users": users,
            "opportunity": None,
            "action_url": "/opportunities/new",
        },
    )


@router.post("/new")
def create_opportunity(
    request: Request,
    title: str = Form(...),
    customer_id: int = Form(...),
    stage_id: int = Form(...),
    owner_id: int = Form(...),
    estimated_value: float = Form(0),
    close_probability: int = Form(10),
    source: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    opportunity = Opportunity(
        title=title,
        customer_id=customer_id,
        stage_id=stage_id,
        owner_id=owner_id,
        estimated_value=estimated_value,
        close_probability=close_probability,
        source=source,
        notes=notes,
    )
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    register_audit(db, user.email, "create", "opportunity", str(opportunity.id), f"Oportunidade {opportunity.title} criada")
    return RedirectResponse(url="/opportunities/", status_code=303)


@router.get("/{opportunity_id}/edit", response_class=HTMLResponse)
def edit_opportunity_page(opportunity_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    customers = db.execute(select(Customer).order_by(Customer.legal_name)).scalars().all()
    stages = db.execute(select(PipelineStage).order_by(PipelineStage.position)).scalars().all()
    users = db.execute(select(User).order_by(User.full_name)).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "opportunities/form.html",
        {
            "request": request,
            "user": user,
            "customers": customers,
            "stages": stages,
            "users": users,
            "opportunity": opportunity,
            "action_url": f"/opportunities/{opportunity_id}/edit",
        },
    )


@router.post("/{opportunity_id}/edit")
def edit_opportunity(
    opportunity_id: int,
    request: Request,
    title: str = Form(...),
    customer_id: int = Form(...),
    stage_id: int = Form(...),
    owner_id: int = Form(...),
    estimated_value: float = Form(0),
    close_probability: int = Form(10),
    source: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    opportunity.title = title
    opportunity.customer_id = customer_id
    opportunity.stage_id = stage_id
    opportunity.owner_id = owner_id
    opportunity.estimated_value = estimated_value
    opportunity.close_probability = close_probability
    opportunity.source = source
    opportunity.notes = notes

    db.commit()

    register_audit(db, user.email, "update", "opportunity", str(opportunity.id), f"Oportunidade {opportunity.title} atualizada")
    return RedirectResponse(url="/opportunities/", status_code=303)


@router.post("/{opportunity_id}/delete")
def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    opportunity = db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    opportunity_title = opportunity.title
    db.delete(opportunity)
    db.commit()

    register_audit(db, user.email, "delete", "opportunity", str(opportunity_id), f"Oportunidade {opportunity_title} excluída")
    return RedirectResponse(url="/opportunities/", status_code=303)
