"""测试配置：使用内存 SQLite，避免依赖真实数据库；Celery 以 eager 模式运行，无需 broker。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  确保模型注册到 Base.metadata（须在 import app.main 前避免名称遮蔽）
from app.celery_app import celery_app
from app.db import Base, get_db
from app.main import app

# Celery eager 模式：任务同步执行，无需 broker，确保测试可复现
celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)


@pytest.fixture(scope="function")
def db_session():
    """每个测试函数一个隔离的内存数据库；同时 patch app.db.SessionLocal 供 Celery Task 使用。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    import app.db as _app_db
    _orig_session_local = _app_db.SessionLocal
    _app_db.SessionLocal = TestingSession  # Celery eager tasks 使用此 patch 后的 SessionLocal

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        _app_db.SessionLocal = _orig_session_local  # 还原
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    """带 DB 覆盖的测试客户端。"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
