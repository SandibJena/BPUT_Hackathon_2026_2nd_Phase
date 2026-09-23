from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router
from app.core.config import DISCLAIMER, Settings
from app.core.database import build_engine, initialize


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = build_engine(settings.resolved_database_url)
        initialize(engine)
        application.state.engine = engine
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(title='Saathi — Synthetic Triage Foundation',
                          version='0.1.0', description=DISCLAIMER, lifespan=lifespan)
    application.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin],
                               allow_methods=['GET'], allow_headers=['Content-Type'])
    application.include_router(router)
    return application


app = create_app()
