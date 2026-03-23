from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.deps import require_role
from app.models import PricingSetting, PricingTaxRegime, PricingSegment
from app.audit import register_audit

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/", response_class=HTMLResponse)
def pricing_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    pricing_settings = db.execute(select(PricingSetting)).scalar_one_or_none()
    if not pricing_settings:
        pricing_settings = PricingSetting(price_per_invoice=0, price_per_employee=0)
        db.add(pricing_settings)
        db.commit()
        db.refresh(pricing_settings)

    tax_regimes = db.execute(
        select(PricingTaxRegime).order_by(PricingTaxRegime.name)
    ).scalars().all()

    segments = db.execute(
        select(PricingSegment).order_by(PricingSegment.name)
    ).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "pricing/form.html",
        {
            "request": request,
            "user": user,
            "pricing_settings": pricing_settings,
            "tax_regimes": tax_regimes,
            "segments": segments,
        },
    )


@router.post("/settings")
def save_pricing_settings(
    request: Request,
    price_per_invoice: float = Form(...),
    price_per_employee: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    pricing_settings = db.execute(select(PricingSetting)).scalar_one_or_none()
    if not pricing_settings:
        pricing_settings = PricingSetting()

    pricing_settings.price_per_invoice = price_per_invoice
    pricing_settings.price_per_employee = price_per_employee

    db.add(pricing_settings)
    db.commit()

    register_audit(
        db,
        user.email,
        "update",
        "pricing_settings",
        str(pricing_settings.id),
        "Configurações gerais da tabela de preços atualizadas",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/tax-regimes/new")
def create_tax_regime(
    request: Request,
    name: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = PricingTaxRegime(name=name.strip(), amount=amount)
    db.add(row)
    db.commit()

    register_audit(
        db,
        user.email,
        "create",
        "pricing_tax_regime",
        str(row.id),
        f"Regime tributário {row.name} criado",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/tax-regimes/{tax_regime_id}/edit")
def edit_tax_regime(
    tax_regime_id: int,
    request: Request,
    name: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = db.get(PricingTaxRegime, tax_regime_id)
    row.name = name.strip()
    row.amount = amount
    db.commit()

    register_audit(
        db,
        user.email,
        "update",
        "pricing_tax_regime",
        str(row.id),
        f"Regime tributário {row.name} atualizado",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/tax-regimes/{tax_regime_id}/delete")
def delete_tax_regime(
    tax_regime_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = db.get(PricingTaxRegime, tax_regime_id)
    name = row.name
    db.delete(row)
    db.commit()

    register_audit(
        db,
        user.email,
        "delete",
        "pricing_tax_regime",
        str(tax_regime_id),
        f"Regime tributário {name} excluído",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/segments/new")
def create_segment(
    request: Request,
    name: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = PricingSegment(name=name.strip(), amount=amount)
    db.add(row)
    db.commit()

    register_audit(
        db,
        user.email,
        "create",
        "pricing_segment",
        str(row.id),
        f"Segmento {row.name} criado",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/segments/{segment_id}/edit")
def edit_segment(
    segment_id: int,
    request: Request,
    name: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = db.get(PricingSegment, segment_id)
    row.name = name.strip()
    row.amount = amount
    db.commit()

    register_audit(
        db,
        user.email,
        "update",
        "pricing_segment",
        str(row.id),
        f"Segmento {row.name} atualizado",
    )

    return RedirectResponse(url="/pricing/", status_code=303)


@router.post("/segments/{segment_id}/delete")
def delete_segment(
    segment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    row = db.get(PricingSegment, segment_id)
    name = row.name
    db.delete(row)
    db.commit()

    register_audit(
        db,
        user.email,
        "delete",
        "pricing_segment",
        str(segment_id),
        f"Segmento {name} excluído",
    )

    return RedirectResponse(url="/pricing/", status_code=303)