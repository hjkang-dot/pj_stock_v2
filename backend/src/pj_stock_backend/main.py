import threading
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pj_stock_backend.api.routes_health import router as health_router
from pj_stock_backend.api.routes_stocks import router as stocks_router
from pj_stock_backend.api.routes_portfolio import router as portfolio_router
from pj_stock_backend.core.config import settings
from pj_stock_backend.db.sqlite import initialize_database, get_connection
from pj_stock_backend.services.portfolio_service import update_portfolio_to_latest

scheduler_running = False
last_run_date = ""


def daily_scheduler_loop():
    global scheduler_running, last_run_date
    print("[scheduler] Starting daily portfolio scheduler thread...")
    while scheduler_running:
        now = datetime.now()
        # Trigger daily update at 22:00 (10 PM)
        if now.hour == 22 and now.minute == 0 and last_run_date != now.strftime("%Y-%m-%d"):
            print(f"[scheduler] Triggering daily portfolio update: {now}")
            try:
                with get_connection() as conn:
                    res = update_portfolio_to_latest(conn)
                    print(f"[scheduler] Daily portfolio update result: {res}")
                last_run_date = now.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"[scheduler] Error in daily scheduler task: {e}")
        time.sleep(30)
    print("[scheduler] Daily portfolio scheduler thread stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler_running
    # Automatically initialize schemas if not present
    initialize_database()

    # Start background scheduler
    scheduler_running = True
    thread = threading.Thread(target=daily_scheduler_loop, daemon=True)
    thread.start()

    yield

    # Stop background scheduler
    scheduler_running = False


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
app.include_router(portfolio_router)

