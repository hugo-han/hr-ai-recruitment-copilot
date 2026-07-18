"""对象存储抽象：MVP 用本地文件兜底，生产用华为云 OBS。对应 system-design 3.3。

接口：put(key, bytes) / get(key) / delete(key)。
生产实现 OBSClient 需用华为云 SDK + KMS 加密；此处提供 LocalObjectStorage 供开发测试。
"""
import os
import uuid
from pathlib import Path
from typing import Protocol


class ObjectStorage(Protocol):
    def put(self, key: str, data: bytes) -> str: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalObjectStorage:
    """本地文件兜底存储。生产应替换为 OBSClient。"""

    def __init__(self, base_dir: str | None = None):
        self.base = Path(base_dir or os.getenv("OBS_LOCAL_DIR", "./.obs-local"))
        self.base.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: bytes) -> str:
        path = self.base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{path}"

    def get(self, key: str) -> bytes:
        return (self.base / key).read_bytes()

    def delete(self, key: str) -> None:
        path = self.base / key
        if path.exists():
            path.unlink()


def get_storage() -> ObjectStorage:
    """按配置返回存储实现。MVP 统一用本地兜底，生产注入 OBSClient。"""
    return LocalObjectStorage()


def gen_key(file_name: str) -> str:
    ext = Path(file_name).suffix
    return f"resumes/{uuid.uuid4().hex}{ext}"
