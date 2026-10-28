from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from brandproof.approval import router as approval_router
from brandproof.config import Settings
from brandproof.db import make_engine, session_factory
from brandproof.documents import router as documents_router
from brandproof.errors import install_errors
from brandproof.logos import router as logos_router
from brandproof.migrations import migrate
from brandproof.posters import router as posters_router
from brandproof.review_leases import recover_expired
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
        migrate(engine)
        with sessions.begin() as recovery_session:
            recover_expired(recovery_session)
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
    app.include_router(logos_router)
    app.include_router(documents_router)
    app.state.engine = engine
    app.state.sessions = sessions
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-BrandProof-Session",
            "X-BrandProof-Filename",
        ],
    )

    @app.middleware("http")
    async def prevent_session_caching(request, call_next):
        response = await call_next(request)
        if request.url.path.rstrip("/") in (
            "/api/v1/demo-sessions",
            "/api/v1/demo-sessions/resume",
        ):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response

    @app.get("/api/v1/health")
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "version": "0.1.0"}

    # The hash-routed UI and API share one origin, including the recovery cookie.
    # API routes are registered first; only the built public assets are exposed.
    if settings.frontend_dist is not None:
        if not (settings.frontend_dist / "index.html").is_file():
            raise RuntimeError("BRANDPROOF_FRONTEND_DIST must contain a built index.html")
        app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")

    return app
