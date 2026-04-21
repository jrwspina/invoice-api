from celery import Celery
from celery.schedules import crontab

from app.settings import settings

app = Celery("invoice")


app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    enable_utc=True,
)
app.autodiscover_tasks(["app"])

app.conf.beat_schedule = {
    "check-overdue-invoices-daily": {
        "task": "app.tasks.check_overdue_invoices",
        "schedule": crontab(hour=0, minute=0),
    }
}
