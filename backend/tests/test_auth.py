"""认证与鉴权测试。覆盖 TC-101~108。"""
from app.common.security import hash_password
from app.models.enums import Role
from app.models.user import User


def _create_user(db, username="hr1", role=Role.HR, status="active", password="pass123"):
    user = User(
        username=username,
        password_hash=hash_password(password),
        name=username,
        role=role,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_success(client, db_session):
    _create_user(db_session, username="hr1", password="pass123")
    resp = client.post("/api/auth/login", json={"username": "hr1", "password": "pass123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["role"] == "HR"


def test_login_wrong_password(client, db_session):
    _create_user(db_session, username="hr2", password="pass123")
    resp = client.post("/api/auth/login", json={"username": "hr2", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] != 0


def test_login_disabled_user(client, db_session):
    _create_user(db_session, username="hr3", password="pass123", status="disabled")
    resp = client.post("/api/auth/login", json={"username": "hr3", "password": "pass123"})
    assert resp.status_code == 403


def test_password_stored_hashed(client, db_session):
    user = _create_user(db_session, username="hr4", password="pass123")
    assert user.password_hash != "pass123"
    assert "$2" in user.password_hash  # bcrypt 前缀


def test_refresh_success(client, db_session):
    from app.common.security import create_refresh_token

    user = _create_user(db_session, username="hr5", password="pass123")
    rt = create_refresh_token(user.id)
    resp = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, db_session):
    _create_user(db_session, username="hr6", role=Role.HR)
    resp = client.post("/api/auth/login", json={"username": "hr6", "password": "pass123"})
    token = resp.json()["data"]["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == "hr6"


def test_invalid_token_returns_401(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
