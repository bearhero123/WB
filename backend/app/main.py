"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.scheduler_service import (
    apply_all_schedules,
    run_startup_catchup,
    shutdown_scheduler,
    start_scheduler,
)

# Console log output (visible via `docker logs`)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup/shutdown hooks."""
    logger.info("Weibo check-in service starting...")
    start_scheduler()
    await apply_all_schedules()
    await run_startup_catchup()
    logger.info("Startup completed")
    yield
    logger.info("Weibo check-in service shutting down...")
    shutdown_scheduler()
    logger.info("Shutdown completed")


app = FastAPI(
    title="Weibo Super Topic Auto Check-in System",
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

# Routers
from app.api.admin_accounts import router as admin_accounts_router
from app.api.admin_keys import router as admin_keys_router
from app.api.admin_push import router as admin_push_router
from app.api.admin_tasks import router as admin_tasks_router
from app.api.external import router as external_router

app.include_router(external_router)
app.include_router(admin_accounts_router)
app.include_router(admin_keys_router)
app.include_router(admin_tasks_router)
app.include_router(admin_push_router)


@app.get("/api/health")
async def health():
    return {"ok": True, "message": "running"}
