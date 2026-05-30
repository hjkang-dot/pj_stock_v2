from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pj_stock_backend.api.routes_health import router as health_router
from pj_stock_backend.api.routes_stocks import router as stocks_router
from pj_stock_backend.core.config import settings
from pj_stock_backend.db.sqlite import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically initialize schemas if not present
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

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

