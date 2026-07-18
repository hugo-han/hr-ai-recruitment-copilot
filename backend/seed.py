"""种子数据：创建测试用户（开发/验收用）。运行：python seed.py"""
import sys
sys.path.insert(0, ".")

from app.db import SessionLocal
from app.common.security import hash_password
from app.models.user import User
from app.models.enums import Role

USERS = [
    ("admin", "admin123", "系统管理员", Role.ADMIN),
    ("hr", "hr123", "HR 招聘专员", Role.HR),
    ("hr_lead", "lead123", "HR 负责人", Role.HR_LEAD),
    ("interviewer", "iv123", "面试官李四", Role.INTERVIEWER),
]

db = SessionLocal()
try:
    for username, password, name, role in USERS:
        if db.query(User).filter_by(username=username).first():
            print(f"SKIP {username}: 已存在")
            continue
        db.add(User(username=username, password_hash=hash_password(password), name=name, role=role))
        print(f"CREATED {username} ({role.value}): {password}")
    db.commit()
    print("\n测试账号创建完成，可用任一账号登录前端 http://localhost:5173")
finally:
    db.close()
