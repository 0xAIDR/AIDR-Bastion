from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import close_db, init_db
from app.managers import ALL_MANAGERS_MAP
from app.modules.logger import bastion_logger
from app.pipelines import PIPELINES_MAP
from app.routers.events import events_router
from app.routers.flow import flow_router
from app.routers.manager import manager_router
from app.routers.rules import rules_router
from settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Startup
    bastion_logger.info("Starting up AIDR Bastion...")
    await init_db()
    for pipeline in PIPELINES_MAP.values():
        await pipeline.activate()
    bastion_logger.info("AIDR Bastion started successfully")

    yield

    # Shutdown
    bastion_logger.info("Shutting down AIDR Bastion...")
    for manager in ALL_MANAGERS_MAP.values():
        await manager.close_connections()
    await close_db()
    bastion_logger.info("AIDR Bastion stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    description="API for LLM Protection",
    version="1.0.0",
)

# Include all routers with /api/v1 prefix
app.include_router(flow_router, prefix="/api/v1")
app.include_router(manager_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    bastion_logger.info(f"[{settings.PROJECT_NAME}] Server is running: {settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="warning")
