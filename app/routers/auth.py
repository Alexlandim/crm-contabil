from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db
from app.models import User
from app.security import verify_password, sign_session
from app.audit import register_audit

router = APIRouter(tags=["auth"])


def render(request: Request, template: str, **context):
    return request.app.state.templates.TemplateResponse(template, {"request": request, **context})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render(request, "login.html")


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return render(request, "login.html", error="Credenciais inválidas")

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=request.app.state.settings.session_cookie_name,
        value=sign_session({"user_id": user.id}),
        httponly=True,
        samesite="lax",
    )
    register_audit(db, user.email, "login", "user", str(user.id), "Login realizado")
    return response


@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(request.app.state.settings.session_cookie_name)
    return response
