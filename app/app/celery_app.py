import os
import time

import celery
import ddtrace

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

if os.environ.get("DATADOG_API_KEY"):
    ddtrace.patch_all()

app = celery.Celery("uptime")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    time.sleep(3)
    return {"uptime": "it's all looking up from here"}
