"""安全工具: SHA256 哈希、Key 生成"""

import hashlib
import uuid


def generate_member_key() -> str:
    """生成随机会员 Key 明文"""
    return str(uuid.uuid4())


def hash_key(plain_key: str) -> str:
    """SHA-256 哈希"""
    return hashlib.sha256(plain_key.encode("utf-8")).hexdigest()
