from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings.duckdb_abs_path.parent.mkdir(parents=True, exist_ok=True)

    from app.db.connection import db_manager

    db_manager.initialize(settings.duckdb_abs_path)
    yield
    db_manager.close()


def create_app() -> FastAPI:
    app = FastAPI(title="AnalystOS", version="0.1.0", lifespan=lifespan)

    allowed_origins = [settings.frontend_url]
    if settings.allowed_origins:
        allowed_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.routes import router as api_router

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
