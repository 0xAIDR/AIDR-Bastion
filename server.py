from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.logger import pipeline_logger
from app.modules.opensearch import os_client
from app.routers.pipeline import pipeline_router
from settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Initialize OpenSearch client if configured
    if settings.OS:
        await os_client.connect()

    # Initialize vector backends for similarity pipeline
    try:
        from app.pipelines.similarity_pipeline.backends.factory import VectorBackendFactory
        backend = VectorBackendFactory.create_backend(settings.VECTOR_BACKEND)
        if backend:
            await backend.connect()
            pipeline_logger.info(f"Vector backend {backend.backend_name} initialized successfully")
    except Exception as e:
        pipeline_logger.error(f"Failed to initialize vector backend: {e}")

    yield

    # Cleanup connections
    if settings.OS:
        await os_client.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, description="API for LLM Protection", version="1.0.0")

app.include_router(pipeline_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="warning")
    pipeline_logger.info("Server is running: %s:%s", settings.HOST, settings.PORT)
