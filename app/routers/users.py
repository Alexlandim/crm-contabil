from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.deps import require_role
from app.models import User, Role
from app.audit import register_audit
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    users = db.execute(select(User).order_by(User.id.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "user": user,
            "users": users,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": user,
            "roles": roles,
            "target_user": None,
            "action_url": "/users/new",
        },
    )


@router.post("/new")
def create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    existing = db.execute(
        select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()

    if existing:
        roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
        return request.app.state.templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "target_user": None,
                "action_url": "/users/new",
                "error": "Já existe um usuário com este e-mail.",
            },
            status_code=400,
        )

    new_user = User(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role_id=role_id,
        is_active=bool(is_active),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    register_audit(
        db,
        user.email,
        "create",
        "user",
        str(new_user.id),
        f"Usuário {new_user.email} criado",
    )
    return RedirectResponse(url="/users/", status_code=303)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
def edit_user_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    return request.app.state.templates.TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": user,
            "roles": roles,
            "target_user": target_user,
            "action_url": f"/users/{user_id}/edit",
        },
    )


@router.post("/{user_id}/edit")
def edit_user(
    user_id: int,
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    role_id: int = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    existing = db.execute(
        select(User).where(User.email == email.strip().lower(), User.id != user_id)
    ).scalar_one_or_none()

    if existing:
        roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
        return request.app.state.templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": user,
                "roles": roles,
                "target_user": target_user,
                "action_url": f"/users/{user_id}/edit",
                "error": "Já existe outro usuário com este e-mail.",
            },
            status_code=400,
        )

    target_user.full_name = full_name.strip()
    target_user.email = email.strip().lower()
    target_user.role_id = role_id
    target_user.is_active = bool(is_active)

    if password.strip():
        target_user.password_hash = hash_password(password.strip())

    db.commit()

    register_audit(
        db,
        user.email,
        "update",
        "user",
        str(target_user.id),
        f"Usuário {target_user.email} atualizado",
    )
    return RedirectResponse(url="/users/", status_code=303)


@router.post("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if target_user.id == user.id:
        raise HTTPException(status_code=400, detail="Você não pode inativar seu próprio usuário por aqui.")

    target_user.is_active = not target_user.is_active
    db.commit()

    register_audit(
        db,
        user.email,
        "toggle_active",
        "user",
        str(target_user.id),
        f"Usuário {target_user.email} alterado para {'ativo' if target_user.is_active else 'inativo'}",
    )
    return RedirectResponse(url="/users/", status_code=303)


@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if target_user.id == user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário.")

    user_email = target_user.email
    db.delete(target_user)
    db.commit()

    register_audit(
        db,
        user.email,
        "delete",
        "user",
        str(user_id),
        f"Usuário {user_email} excluído",
    )
    return RedirectResponse(url="/users/", status_code=303)