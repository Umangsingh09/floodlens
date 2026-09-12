import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.region import router as region_router
from app.api.risk import router as risk_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_scheduled_refresh() -> None:
    from ai.inference.predict_current_risk import run_prediction

    try:
        run_prediction()
    except Exception:  # noqa: BLE001 - a failed scheduled run must never crash the process
        logger.exception("Scheduled risk refresh failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _scheduler
    # PYTEST_CURRENT_TEST is set by pytest for the duration of every test; skip starting a
    # background job that makes live Earth Engine calls while running the test suite.
    if settings.enable_scheduler and not os.environ.get("PYTEST_CURRENT_TEST"):
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            _run_scheduled_refresh,
            "interval",
            hours=settings.risk_refresh_interval_hours,
            id="risk_refresh",
        )
        _scheduler.start()
        logger.info("Risk refresh scheduler started (every %sh)", settings.risk_refresh_interval_hours)
    yield
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(region_router, prefix="/api")
app.include_router(events_router, prefix="/api")
