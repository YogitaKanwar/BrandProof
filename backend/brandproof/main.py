from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from brandproof.approval import router as approval_router
from brandproof.config import Settings
from brandproof.db import Base, make_engine, session_factory
from brandproof.errors import install_errors
from brandproof.posters import router as posters_router
from brandproof.reviews import router as reviews_router
from brandproof.routes import router
from brandproof.sources import router as sources_router
from brandproof.suggestions import router as suggestions_router
from brandproof.workflow import router as workflow_router


def create_app(*, database_url: str | None = None):
    settings = Settings()
    engine = make_engine(database_url or settings.database_url)
    sessions = session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="BrandProof API", version="0.1.0", lifespan=lifespan)
    install_errors(app)
    app.include_router(router)
    app.include_router(sources_router)
    app.include_router(reviews_router)
    app.include_router(workflow_router)
    app.include_router(approval_router)
    app.include_router(suggestions_router)
    app.include_router(posters_router)
    app.state.engine = engine
    app.state.sessions = sessions
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/api/v1/health")
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "version": "0.1.0"}

    return app
