from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import ProposalBaseTemplate
from app.services.document_service import get_default_template_texts

router = APIRouter(prefix="/proposal-base", tags=["proposal-base"])


@router.get("/", response_class=HTMLResponse)
def list_templates(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    templates = db.execute(
        select(ProposalBaseTemplate).order_by(ProposalBaseTemplate.id.desc())
    ).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "proposal_base/list.html",
        {
            "request": request,
            "templates": templates,
            "user": user,
            "defaults": get_default_template_texts(),
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_template(
    request: Request,
    user=Depends(get_current_user),
):
    return request.app.state.templates.TemplateResponse(
        "proposal_base/form.html",
        {
            "request": request,
            "template": None,
            "action_url": "/proposal-base/new",
            "user": user,
            "defaults": get_default_template_texts(),
        },
    )


@router.post("/new")
def create_template(
    name: str = Form(...),
    presentation: str = Form(""),
    methodology: str = Form(""),
    services_description: str = Form(""),
    extra_services: str = Form(""),
    closing: str = Form(""),
    general_conditions: str = Form(""),
    is_active: bool = Form(False),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if is_active:
        active_templates = db.execute(
            select(ProposalBaseTemplate).where(ProposalBaseTemplate.is_active == True)
        ).scalars().all()
        for item in active_templates:
            item.is_active = False

    template = ProposalBaseTemplate(
        name=name,
        presentation=presentation,
        methodology=methodology,
        services_description=services_description,
        extra_services=extra_services,
        closing=closing,
        general_conditions=general_conditions,
        is_active=is_active,
    )

    db.add(template)
    db.commit()

    return RedirectResponse("/proposal-base/", status_code=303)


@router.get("/{template_id}/edit", response_class=HTMLResponse)
def edit_template_page(
    template_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    template = db.get(ProposalBaseTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Base da proposta não encontrada")

    return request.app.state.templates.TemplateResponse(
        "proposal_base/form.html",
        {
            "request": request,
            "template": template,
            "action_url": f"/proposal-base/{template_id}/edit",
            "user": user,
            "defaults": get_default_template_texts(),
        },
    )


@router.post("/{template_id}/edit")
def edit_template(
    template_id: int,
    name: str = Form(...),
    presentation: str = Form(""),
    methodology: str = Form(""),
    services_description: str = Form(""),
    extra_services: str = Form(""),
    closing: str = Form(""),
    general_conditions: str = Form(""),
    is_active: bool = Form(False),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    template = db.get(ProposalBaseTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Base da proposta não encontrada")

    if is_active:
        active_templates = db.execute(
            select(ProposalBaseTemplate).where(
                ProposalBaseTemplate.is_active == True,
                ProposalBaseTemplate.id != template_id,
            )
        ).scalars().all()
        for item in active_templates:
            item.is_active = False

    template.name = name
    template.presentation = presentation
    template.methodology = methodology
    template.services_description = services_description
    template.extra_services = extra_services
    template.closing = closing
    template.general_conditions = general_conditions
    template.is_active = is_active

    db.commit()

    return RedirectResponse("/proposal-base/", status_code=303)