from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.deps import get_current_user
from app.models import (
    Proposal,
    ProposalItem,
    Customer,
    Product,
    CompanySetting,
    ProposalBaseTemplate,
    ProposalDocumentBase,
)
from app.audit import register_audit
from app.services.proposal_service import (
    generate_proposal_number,
    recalculate_proposal,
    duplicate_proposal,
)
from app.services.document_service import export_proposal_docx, export_proposal_pdf
from app.services.pricing_service import calculate_suggested_price, get_pricing_snapshot

router = APIRouter(prefix="/proposals", tags=["proposals"])


def get_active_base_template(db: Session) -> ProposalBaseTemplate | None:
    return db.execute(
        select(ProposalBaseTemplate)
        .where(ProposalBaseTemplate.is_active == True)
        .order_by(ProposalBaseTemplate.id.desc())
    ).scalars().first()


def sync_proposal_document_base(db: Session, proposal: Proposal) -> ProposalDocumentBase:
    active_template = get_active_base_template(db)

    snapshot = proposal.document_base
    if not snapshot:
        snapshot = ProposalDocumentBase(proposal_id=proposal.id)
        db.add(snapshot)

    if active_template:
        snapshot.template_name = active_template.name or "Base padrão"
        snapshot.presentation = active_template.presentation or ""
        snapshot.methodology = active_template.methodology or ""
        snapshot.services_description = active_template.services_description or ""
        snapshot.extra_services = active_template.extra_services or ""
        snapshot.closing = active_template.closing or ""
        snapshot.general_conditions = active_template.general_conditions or ""
    else:
        snapshot.template_name = "Base padrão"
        snapshot.presentation = snapshot.presentation or ""
        snapshot.methodology = snapshot.methodology or ""
        snapshot.services_description = snapshot.services_description or ""
        snapshot.extra_services = snapshot.extra_services or ""
        snapshot.closing = snapshot.closing or ""
        snapshot.general_conditions = snapshot.general_conditions or ""

    db.flush()
    return snapshot


def copy_document_base_snapshot(
    db: Session,
    original: Proposal,
    duplicated: Proposal,
) -> None:
    if original.document_base:
        db.add(
            ProposalDocumentBase(
                proposal_id=duplicated.id,
                template_name=original.document_base.template_name or "Base padrão",
                presentation=original.document_base.presentation or "",
                methodology=original.document_base.methodology or "",
                services_description=original.document_base.services_description or "",
                extra_services=original.document_base.extra_services or "",
                closing=original.document_base.closing or "",
                general_conditions=original.document_base.general_conditions or "",
            )
        )
        db.commit()
        return

    sync_proposal_document_base(db, duplicated)
    db.commit()


@router.get("/", response_class=HTMLResponse)
def list_proposals(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposals = db.execute(select(Proposal).order_by(Proposal.id.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "proposals/list.html",
        {
            "request": request,
            "user": user,
            "proposals": proposals,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_proposal(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    customers = db.execute(
        select(Customer).order_by(Customer.legal_name)
    ).scalars().all()

    products = db.execute(
        select(Product).where(Product.is_active == True).order_by(Product.name)
    ).scalars().all()

    settings = db.execute(select(CompanySetting)).scalar_one_or_none()
    proposal_number = generate_proposal_number(db)
    pricing_snapshot = get_pricing_snapshot(db)

    validity_days = settings.default_validity_days if settings else 15

    return request.app.state.templates.TemplateResponse(
        "proposals/form.html",
        {
            "request": request,
            "user": user,
            "customers": customers,
            "products": products,
            "proposal": None,
            "proposal_number": proposal_number,
            "validity_date": date.today() + timedelta(days=validity_days),
            "action_url": "/proposals/new",
            "suggested_pricing": {
                "regime_value": 0,
                "segment_value": 0,
                "invoices_value": 0,
                "employees_value": 0,
                "suggested_price": 0,
                "price_per_invoice": pricing_snapshot["price_per_invoice"],
                "price_per_employee": pricing_snapshot["price_per_employee"],
            },
            "pricing_snapshot": pricing_snapshot,
        },
    )


@router.post("/new")
def create_proposal(
    request: Request,
    customer_id: int = Form(...),
    proposal_number: str = Form(...),
    issue_date: str = Form(...),
    validity_date: str = Form(...),
    cnpj: str = Form(""),
    faturamento: str = Form(""),
    tax_regime: str = Form(""),
    business_segment: str = Form(""),
    employee_count: int = Form(0),
    monthly_revenue_avg: float = Form(0),
    monthly_invoices_avg: int = Form(0),
    notes: str = Form(""),
    global_discount: float = Form(0),
    product_ids: list[int] = Form(...),
    descriptions: list[str] = Form(...),
    quantities: list[float] = Form(...),
    unit_prices: list[float] = Form(...),
    discount_amounts: list[float] = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    suggested_pricing = calculate_suggested_price(
        db=db,
        tax_regime=tax_regime,
        business_segment=business_segment,
        monthly_invoices_avg=monthly_invoices_avg,
        employee_count=employee_count,
    )

    proposal = Proposal(
        customer_id=customer_id,
        owner_id=user.id,
        proposal_number=proposal_number,
        issue_date=date.fromisoformat(issue_date),
        validity_date=date.fromisoformat(validity_date),
        cnpj=cnpj,
        faturamento=faturamento,
        tax_regime=tax_regime,
        business_segment=business_segment,
        employee_count=employee_count,
        monthly_revenue_avg=monthly_revenue_avg,
        monthly_invoices_avg=monthly_invoices_avg,
        notes=notes,
        global_discount=global_discount,
        status="rascunho",
    )
    db.add(proposal)
    db.flush()

    for product_id, description, quantity, unit_price, discount_amount in zip(
        product_ids,
        descriptions,
        quantities,
        unit_prices,
        discount_amounts,
    ):
        if quantity <= 0 or unit_price < 0:
            continue

        db.add(
            ProposalItem(
                proposal_id=proposal.id,
                product_id=product_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount_amount,
            )
        )

    db.flush()
    db.refresh(proposal)
    recalculate_proposal(proposal)
    sync_proposal_document_base(db, proposal)
    db.commit()
    db.refresh(proposal)

    register_audit(
        db,
        user.email,
        "create",
        "proposal",
        str(proposal.id),
        f"Proposta {proposal.proposal_number} criada. Preço sugerido: R$ {suggested_pricing['suggested_price']:.2f}",
    )

    return RedirectResponse(url=f"/proposals/{proposal.id}", status_code=303)


@router.get("/pricing-preview")
def pricing_preview(
    tax_regime: str = Query(""),
    business_segment: str = Query(""),
    monthly_invoices_avg: int = Query(0),
    employee_count: int = Query(0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    suggested_pricing = calculate_suggested_price(
        db=db,
        tax_regime=tax_regime or "",
        business_segment=business_segment or "",
        monthly_invoices_avg=max(monthly_invoices_avg or 0, 0),
        employee_count=max(employee_count or 0, 0),
    )

    return JSONResponse(
        {
            "regime_value": float(suggested_pricing["regime_value"]),
            "segment_value": float(suggested_pricing["segment_value"]),
            "invoices_value": float(suggested_pricing["invoices_value"]),
            "employees_value": float(suggested_pricing["employees_value"]),
            "price_per_invoice": float(suggested_pricing["price_per_invoice"]),
            "price_per_employee": float(suggested_pricing["price_per_employee"]),
            "suggested_price": float(suggested_pricing["suggested_price"]),
        }
    )


@router.get("/{proposal_id}/edit", response_class=HTMLResponse)
def edit_proposal_page(
    proposal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    customers = db.execute(
        select(Customer).order_by(Customer.legal_name)
    ).scalars().all()

    products = db.execute(
        select(Product).where(Product.is_active == True).order_by(Product.name)
    ).scalars().all()

    suggested_pricing = calculate_suggested_price(
        db=db,
        tax_regime=proposal.tax_regime,
        business_segment=proposal.business_segment,
        monthly_invoices_avg=proposal.monthly_invoices_avg,
        employee_count=proposal.employee_count,
    )
    pricing_snapshot = get_pricing_snapshot(db)

    return request.app.state.templates.TemplateResponse(
        "proposals/form.html",
        {
            "request": request,
            "user": user,
            "customers": customers,
            "products": products,
            "proposal": proposal,
            "proposal_number": proposal.proposal_number,
            "validity_date": proposal.validity_date,
            "action_url": f"/proposals/{proposal_id}/edit",
            "suggested_pricing": suggested_pricing,
            "pricing_snapshot": pricing_snapshot,
        },
    )


@router.post("/{proposal_id}/edit")
def edit_proposal(
    proposal_id: int,
    request: Request,
    customer_id: int = Form(...),
    proposal_number: str = Form(...),
    issue_date: str = Form(...),
    validity_date: str = Form(...),
    cnpj: str = Form(""),
    faturamento: str = Form(""),
    tax_regime: str = Form(""),
    business_segment: str = Form(""),
    employee_count: int = Form(0),
    monthly_revenue_avg: float = Form(0),
    monthly_invoices_avg: int = Form(0),
    notes: str = Form(""),
    global_discount: float = Form(0),
    product_ids: list[int] = Form(...),
    descriptions: list[str] = Form(...),
    quantities: list[float] = Form(...),
    unit_prices: list[float] = Form(...),
    discount_amounts: list[float] = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    suggested_pricing = calculate_suggested_price(
        db=db,
        tax_regime=tax_regime,
        business_segment=business_segment,
        monthly_invoices_avg=monthly_invoices_avg,
        employee_count=employee_count,
    )

    proposal.customer_id = customer_id
    proposal.proposal_number = proposal_number
    proposal.issue_date = date.fromisoformat(issue_date)
    proposal.validity_date = date.fromisoformat(validity_date)
    proposal.cnpj = cnpj
    proposal.faturamento = faturamento
    proposal.tax_regime = tax_regime
    proposal.business_segment = business_segment
    proposal.employee_count = employee_count
    proposal.monthly_revenue_avg = monthly_revenue_avg
    proposal.monthly_invoices_avg = monthly_invoices_avg
    proposal.notes = notes
    proposal.global_discount = global_discount
    proposal.version = (proposal.version or 1) + 1

    for item in list(proposal.items):
        db.delete(item)

    db.flush()

    for product_id, description, quantity, unit_price, discount_amount in zip(
        product_ids,
        descriptions,
        quantities,
        unit_prices,
        discount_amounts,
    ):
        if quantity <= 0 or unit_price < 0:
            continue

        db.add(
            ProposalItem(
                proposal_id=proposal.id,
                product_id=product_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount_amount,
            )
        )

    db.flush()
    db.refresh(proposal)
    recalculate_proposal(proposal)
    sync_proposal_document_base(db, proposal)
    db.commit()
    db.refresh(proposal)

    register_audit(
        db,
        user.email,
        "update",
        "proposal",
        str(proposal.id),
        f"Proposta {proposal.proposal_number} atualizada. Preço sugerido: R$ {suggested_pricing['suggested_price']:.2f}",
    )

    return RedirectResponse(url=f"/proposals/{proposal.id}", status_code=303)


@router.post("/{proposal_id}/delete")
def delete_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    proposal_number = proposal.proposal_number
    db.delete(proposal)
    db.commit()

    register_audit(
        db,
        user.email,
        "delete",
        "proposal",
        str(proposal_id),
        f"Proposta {proposal_number} excluída",
    )

    return RedirectResponse(url="/proposals/", status_code=303)


@router.get("/{proposal_id}", response_class=HTMLResponse)
def view_proposal(
    proposal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    suggested_pricing = calculate_suggested_price(
        db=db,
        tax_regime=proposal.tax_regime,
        business_segment=proposal.business_segment,
        monthly_invoices_avg=proposal.monthly_invoices_avg,
        employee_count=proposal.employee_count,
    )

    return request.app.state.templates.TemplateResponse(
        "proposals/view.html",
        {
            "request": request,
            "user": user,
            "proposal": proposal,
            "suggested_pricing": suggested_pricing,
        },
    )


@router.get("/{proposal_id}/duplicate")
def duplicate(
    proposal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    original = db.get(Proposal, proposal_id)
    if not original:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    new_proposal = duplicate_proposal(db, original)
    copy_document_base_snapshot(db, original, new_proposal)

    register_audit(
        db,
        user.email,
        "duplicate",
        "proposal",
        str(new_proposal.id),
        f"Duplicada de {original.proposal_number}",
    )

    return RedirectResponse(url=f"/proposals/{new_proposal.id}", status_code=303)


@router.get("/{proposal_id}/status/{new_status}")
def change_status(
    proposal_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    allowed = {
        "rascunho",
        "em_revisao",
        "aprovada",
        "enviada",
        "aceita",
        "recusada",
        "vencida",
        "cancelada",
    }

    if new_status in allowed:
        proposal.status = new_status
        db.commit()
        register_audit(
            db,
            user.email,
            "status_change",
            "proposal",
            str(proposal.id),
            f"Status alterado para {new_status}",
        )

    return RedirectResponse(url=f"/proposals/{proposal.id}", status_code=303)




@router.get("/{proposal_id}/pdf")
def proposal_pdf(
    proposal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    output = Path("uploads") / f"proposal_{proposal.id}.pdf"
    export_proposal_pdf(db, proposal, str(output))

    register_audit(
        db,
        user.email,
        "export_pdf",
        "proposal",
        str(proposal.id),
        f"PDF gerado para {proposal.proposal_number}",
    )

    return FileResponse(
        path=output,
        filename=output.name,
        media_type="application/pdf",
    )

@router.get("/{proposal_id}/docx")
def proposal_docx(
    proposal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    output = Path("uploads") / f"proposal_{proposal.id}.docx"
    export_proposal_docx(db, proposal, str(output))

    register_audit(
        db,
        user.email,
        "export_docx",
        "proposal",
        str(proposal.id),
        f"DOCX gerado para {proposal.proposal_number}",
    )

    return FileResponse(
        path=output,
        filename=output.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )