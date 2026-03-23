from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import get_current_user
from app.models import Customer
from app.audit import register_audit

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_class=HTMLResponse)
def list_customers(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    customers = db.execute(select(Customer).order_by(Customer.id.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "customers/list.html",
        {"request": request, "user": user, "customers": customers},
    )


@router.get("/new", response_class=HTMLResponse)
def new_customer(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse(
        "customers/form.html",
        {"request": request, "user": user, "customer": None, "action_url": "/customers/new"},
    )


@router.post("/new")
def create_customer(
    request: Request,
    legal_name: str = Form(...),
    kind: str = Form("lead"),
    trade_name: str = Form(""),
    document: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    whatsapp: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    segment: str = Form(""),
    contact_name: str = Form(""),
    contact_role: str = Form(""),
    lead_source: str = Form(""),
    relationship_status: str = Form("ativo"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    customer = Customer(
        legal_name=legal_name,
        kind=kind,
        trade_name=trade_name,
        document=document,
        email=email,
        phone=phone,
        whatsapp=whatsapp,
        city=city,
        state=state,
        segment=segment,
        contact_name=contact_name,
        contact_role=contact_role,
        lead_source=lead_source,
        relationship_status=relationship_status,
        notes=notes,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    register_audit(db, user.email, "create", "customer", str(customer.id), f"Cliente {customer.legal_name} criado")
    return RedirectResponse(url="/customers/", status_code=303)


@router.get("/{customer_id}/edit", response_class=HTMLResponse)
def edit_customer_page(customer_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    return request.app.state.templates.TemplateResponse(
        "customers/form.html",
        {
            "request": request,
            "user": user,
            "customer": customer,
            "action_url": f"/customers/{customer_id}/edit",
        },
    )


@router.post("/{customer_id}/edit")
def edit_customer(
    customer_id: int,
    request: Request,
    legal_name: str = Form(...),
    kind: str = Form("lead"),
    trade_name: str = Form(""),
    document: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    whatsapp: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    segment: str = Form(""),
    contact_name: str = Form(""),
    contact_role: str = Form(""),
    lead_source: str = Form(""),
    relationship_status: str = Form("ativo"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    customer.legal_name = legal_name
    customer.kind = kind
    customer.trade_name = trade_name
    customer.document = document
    customer.email = email
    customer.phone = phone
    customer.whatsapp = whatsapp
    customer.city = city
    customer.state = state
    customer.segment = segment
    customer.contact_name = contact_name
    customer.contact_role = contact_role
    customer.lead_source = lead_source
    customer.relationship_status = relationship_status
    customer.notes = notes

    db.commit()

    register_audit(db, user.email, "update", "customer", str(customer.id), f"Cliente {customer.legal_name} atualizado")
    return RedirectResponse(url="/customers/", status_code=303)


@router.post("/{customer_id}/delete")
def delete_customer(customer_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    customer_name = customer.legal_name
    db.delete(customer)
    db.commit()

    register_audit(db, user.email, "delete", "customer", str(customer_id), f"Cliente {customer_name} excluído")
    return RedirectResponse(url="/customers/", status_code=303)