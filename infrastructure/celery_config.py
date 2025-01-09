from celery import Celery
from core.config.settings import config

celery_app = Celery(
    "backtest",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    worker_prefetch_multiplier=1,  # One task per worker at a time
    task_routes={
        "backtest.tasks.optimization.*": {"queue": "optimization"},
        "backtest.tasks.data_processing.*": {"queue": "data_processing"},
    },
)
