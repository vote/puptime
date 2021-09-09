#!/bin/bash

# Uncomment and have this command run the following to restore DataDog logging
# ddtrace-run
celery -A app.celery_beat beat --scheduler redbeat.RedBeatScheduler --pidfile="/app/celerybeat-checkable.pid"
