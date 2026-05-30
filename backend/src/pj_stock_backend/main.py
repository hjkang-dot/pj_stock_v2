from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pj_stock_backend.api.routes_health import router as health_router
from pj_stock_backend.api.routes_stocks import router as stocks_router
from pj_stock_backend.core.config import settings

app = FastAPI(title=settings.app_name)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(stocks_router)

