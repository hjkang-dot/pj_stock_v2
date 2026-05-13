from fastapi import FastAPI

from pj_stock_backend.api.routes_health import router as health_router
from pj_stock_backend.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
