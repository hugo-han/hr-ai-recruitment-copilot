"""健康检查测试。"""
from app.common.response import ok


def test_ok_helper():
    assert ok({"x": 1}) == {"code": 0, "message": "ok", "data": {"x": 1}}


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "healthy"
