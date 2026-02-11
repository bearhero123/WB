"""应用配置 - 从环境变量读取"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://weibo:weibo_password@db:5432/weibo"

    # 管理员 API Key
    ADMIN_API_KEY: str = "change-me-to-a-strong-random-key"

    # Server酱推送默认 SendKey
    DEFAULT_SENDKEY: str = ""

    # 签到策略: cardlist 或 topicsub
    CHECKIN_PROVIDER: str = "cardlist"

    # 微博 API 抓包参数 (JSON 字符串)
    WEIBO_API_PARAMS: str = "{}"

    # 时区
    TZ: str = "Asia/Shanghai"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
