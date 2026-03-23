from sqlalchemy.orm import Session
from app.models import AuditLog


def register_audit(db: Session, user_email: str, action: str, entity: str, entity_id: str = "", description: str = ""):
    log = AuditLog(
        user_email=user_email,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description,
    )
    db.add(log)
    db.commit()
