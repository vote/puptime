#!/bin/bash

ddtrace-run celery -A app.celery_beat beat --scheduler redbeat.RedBeatScheduler --pidfile="/app/celerybeat-checkable.pid"
