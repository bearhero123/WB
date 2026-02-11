"""SQLAlchemy 异步数据库配置"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入: 获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
