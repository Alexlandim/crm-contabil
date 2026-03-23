from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.deps import get_current_user
from app.models import Product
from app.audit import register_audit

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_class=HTMLResponse)
def list_products(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    products = db.execute(select(Product).order_by(Product.id.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "products/list.html",
        {"request": request, "user": user, "products": products},
    )


@router.get("/new", response_class=HTMLResponse)
def new_product(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse(
        "products/form.html",
        {"request": request, "user": user, "product": None, "action_url": "/products/new"},
    )


@router.post("/new")
def create_product(
    request: Request,
    internal_code: str = Form(...),
    name: str = Form(...),
    category: str = Form(""),
    commercial_description: str = Form(""),
    technical_description: str = Form(""),
    unit: str = Form("UN"),
    base_price: float = Form(0),
    estimated_cost: float = Form(0),
    max_discount_percent: float = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    product = Product(
        internal_code=internal_code,
        name=name,
        category=category,
        commercial_description=commercial_description,
        technical_description=technical_description,
        unit=unit,
        base_price=base_price,
        estimated_cost=estimated_cost,
        max_discount_percent=max_discount_percent,
        notes=notes,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    register_audit(db, user.email, "create", "product", str(product.id), f"Produto {product.name} criado")
    return RedirectResponse(url="/products/", status_code=303)


@router.get("/{product_id}/edit", response_class=HTMLResponse)
def edit_product_page(product_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return request.app.state.templates.TemplateResponse(
        "products/form.html",
        {
            "request": request,
            "user": user,
            "product": product,
            "action_url": f"/products/{product_id}/edit",
        },
    )


@router.post("/{product_id}/edit")
def edit_product(
    product_id: int,
    request: Request,
    internal_code: str = Form(...),
    name: str = Form(...),
    category: str = Form(""),
    commercial_description: str = Form(""),
    technical_description: str = Form(""),
    unit: str = Form("UN"),
    base_price: float = Form(0),
    estimated_cost: float = Form(0),
    max_discount_percent: float = Form(0),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    product.internal_code = internal_code
    product.name = name
    product.category = category
    product.commercial_description = commercial_description
    product.technical_description = technical_description
    product.unit = unit
    product.base_price = base_price
    product.estimated_cost = estimated_cost
    product.max_discount_percent = max_discount_percent
    product.notes = notes

    db.commit()

    register_audit(db, user.email, "update", "product", str(product.id), f"Produto {product.name} atualizado")
    return RedirectResponse(url="/products/", status_code=303)


@router.post("/{product_id}/delete")
def delete_product(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    product_name = product.name
    db.delete(product)
    db.commit()

    register_audit(db, user.email, "delete", "product", str(product_id), f"Produto {product_name} excluído")
    return RedirectResponse(url="/products/", status_code=303)