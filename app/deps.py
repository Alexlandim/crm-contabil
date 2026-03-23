from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.security import unsign_session
from app.models import User
from app.config import get_settings

settings = get_settings()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="Não autenticado")

    try:
        data = unsign_session(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida") from exc

    user = db.get(User, data.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
    return user


def require_role(*allowed_roles: str):
    def dependency(user: User = Depends(get_current_user)):
        if user.role.name not in allowed_roles:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return user
    return dependency
