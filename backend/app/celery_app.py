import sentry_sdk
from celery import Celery

from app.config import settings

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

celery_app = Celery("pulse", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# DB-driven scheduler: one light tick enqueues every monitor that is due.
celery_app.conf.beat_schedule = {
    "dispatch-due-checks": {
        "task": "app.tasks.dispatch_due_checks",
        "schedule": 10.0,
    },
}

# Imports app/tasks.py so @celery_app.task registrations load in worker + beat.
celery_app.autodiscover_tasks(["app"])
