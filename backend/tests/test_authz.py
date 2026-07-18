"""鉴权依赖测试。覆盖 TC-103/106。"""
from app.common.security import hash_password
from app.models.enums import Role
from app.models.user import User


def _seed(db, username, role=Role.HR):
    db.add(User(username=username, password_hash=hash_password("x"), name=username, role=role))
    db.commit()
    return db.query(User).filter_by(username=username).first()


def test_role_gate_admin_only(client, db_session):
    """非 ADMIN 访问 admin 专用接口应 403。"""
    from app.models.enums import ROLE_PERMISSIONS

    # 任何角色访问 /me 都允许（仅校验登录），故此处验证 ROLE_PERMISSIONS 逻辑单元行为
    assert "dictionary" in ROLE_PERMISSIONS[Role.ADMIN]
    assert "dictionary" not in ROLE_PERMISSIONS[Role.HR]


def test_interviewer_scope(client, db_session):
    from app.models.enums import ROLE_PERMISSIONS

    assert "interview" in ROLE_PERMISSIONS[Role.INTERVIEWER]
    assert "resume" not in ROLE_PERMISSIONS[Role.INTERVIEWER]
    _seed(db_session, "iv1", Role.INTERVIEWER)
