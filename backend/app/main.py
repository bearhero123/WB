"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.scheduler_service import (
    apply_all_schedules,
    start_scheduler,
    shutdown_scheduler,
)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("微博签到系统启动中...")
    start_scheduler()
    await apply_all_schedules()
    logger.info("启动完成")
    yield
    logger.info("微博签到系统关闭中...")
    shutdown_scheduler()
    logger.info("关闭完成")


app = FastAPI(
    title="微博超话自动签到系统",
    version="1.0.0",
    description="Weibo Super Topic Auto Check-in System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.api.external import router as external_router
from app.api.admin_accounts import router as admin_accounts_router
from app.api.admin_keys import router as admin_keys_router
from app.api.admin_tasks import router as admin_tasks_router
from app.api.admin_push import router as admin_push_router

app.include_router(external_router)
app.include_router(admin_accounts_router)
app.include_router(admin_keys_router)
app.include_router(admin_tasks_router)
app.include_router(admin_push_router)


@app.get("/api/health")
async def health():
    return {"ok": True, "message": "系统运行中"}
