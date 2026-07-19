"""种子数据：创建测试用户和默认字典数据（开发/验收用）。运行：python seed.py"""
import sys
sys.path.insert(0, ".")

from app.db import SessionLocal
from app.common.security import hash_password
from app.models.user import User
from app.models.enums import Role
from app.models.dictionary import CompetencyTemplate
from app.models.interview import COMPETENCY_TEMPLATE

USERS = [
    ("admin", "admin123", "系统管理员", Role.ADMIN),
    ("hr", "hr123", "HR 招聘专员", Role.HR),
    ("hr_lead", "lead123", "HR 负责人", Role.HR_LEAD),
    ("interviewer", "iv123", "面试官李四", Role.INTERVIEWER),
]

db = SessionLocal()
try:
    # --- 用户 ---
    for username, password, name, role in USERS:
        if db.query(User).filter_by(username=username).first():
            print(f"SKIP {username}: 已存在")
            continue
        db.add(User(username=username, password_hash=hash_password(password), name=name, role=role))
        print(f"CREATED {username} ({role.value}): {password}")
    db.commit()

    # --- 默认能力评价模板 (Issue #1) ---
    existing_default = db.query(CompetencyTemplate).filter_by(is_default=True, status="active").first()
    expected_dims = [{"name": d} for d in COMPETENCY_TEMPLATE]
    if existing_default:
        existing_names = sorted(
            d["name"] if isinstance(d, dict) else d
            for d in existing_default.dimensions.get("items", [])
        )
        if existing_names != sorted(COMPETENCY_TEMPLATE):
            print(f"WARNING: 默认模板维度 {existing_names} 与 COMPETENCY_TEMPLATE {list(COMPETENCY_TEMPLATE)} 不一致，重建...")
            existing_default.is_default = False
            existing_default.status = "inactive"
            db.commit()
            existing_default = None

    if not existing_default:
        db.add(CompetencyTemplate(
            name="标准面试模板",
            dimensions={"items": expected_dims},
            is_default=True,
            status="active",
        ))
        db.commit()
        print(f"CREATED 默认能力评价模板: {list(COMPETENCY_TEMPLATE)}")
    else:
        print(f"SKIP 默认能力评价模板: 已存在且维度一致")

    print("\n测试账号创建完成，可用任一账号登录前端 http://localhost:5173")
finally:
    db.close()
