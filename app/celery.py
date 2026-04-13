from celery import Celery
from app.settings import settings

app = Celery("invoice")


app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    enable_utc=True,
)
app.autodiscover_tasks(["app"])
