from fastapi import FastAPI

from app.api.routes import expenses
from app.core.errors import register_error_handlers


def create_app() -> FastAPI:
    # Everything lives under /api so the frontend can proxy /api/* to this service with no CORS.
    app = FastAPI(title="Expense Tracker API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    register_error_handlers(app)
    app.include_router(expenses.router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
