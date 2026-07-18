#!/bin/bash
set -e

echo "=== HR Copilot Backend Entrypoint ==="

# 等待 PostgreSQL 就绪
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "Waiting for PostgreSQL..."
    until python -c "from app.db import engine; engine.connect()" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL ready"
fi

# 运行 Alembic 迁移
echo "Running Alembic migrations..."
alembic upgrade head

# 种子数据（幂等，已存在则跳过）
echo "Seeding test users..."
python seed.py

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
