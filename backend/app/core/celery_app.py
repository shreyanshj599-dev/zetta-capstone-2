import platform

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "zetta",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.enrich"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,
    task_soft_time_limit=90,
)

# Windows gotcha: prefork pool spawns workers via fork(), which Windows lacks.
# 'solo' is single-threaded but works on every OS.
if platform.system() == "Windows":
    celery_app.conf.worker_pool = "solo"
