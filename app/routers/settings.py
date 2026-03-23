from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import require_role
from app.models import CompanySetting
from app.audit import register_audit

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_class=HTMLResponse)
def settings_form(request: Request, db: Session = Depends(get_db), user=Depends(require_role("admin", "gestor"))):
    settings = db.execute(select(CompanySetting)).scalar_one()
    return request.app.state.templates.TemplateResponse("settings/form.html", {"request": request, "user": user, "settings": settings})


@router.post("/")
def save_settings(
    request: Request,
    company_name: str = Form(...),
    company_cnpj: str = Form(""),
    company_email: str = Form(""),
    company_phone: str = Form(""),
    company_site: str = Form(""),
    company_address: str = Form(""),
    proposal_footer: str = Form(""),
    default_validity_days: int = Form(15),
    proposal_number_prefix: str = Form("PROP"),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "gestor")),
):
    settings = db.execute(select(CompanySetting)).scalar_one()
    settings.company_name = company_name
    settings.company_cnpj = company_cnpj
    settings.company_email = company_email
    settings.company_phone = company_phone
    settings.company_site = company_site
    settings.company_address = company_address
    settings.proposal_footer = proposal_footer
    settings.default_validity_days = default_validity_days
    settings.proposal_number_prefix = proposal_number_prefix
    db.commit()
    register_audit(db, user.email, "update", "company_settings", str(settings.id), "Configurações atualizadas")
    return RedirectResponse(url="/settings/", status_code=303)
