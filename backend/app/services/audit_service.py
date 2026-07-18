"""通用操作审计服务。对应 Issue #2 / TC-705。"""
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int,
    operator_id: int | None,
    detail: dict | None = None,
) -> AuditLog:
    """写入一条通用操作审计记录，只增不删。"""
    log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        operator_id=operator_id,
        detail=detail,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
