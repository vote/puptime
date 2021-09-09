#!/bin/bash

# Uncomment and have this command run the following to restore DataDog logging
# ddtrace-run
celery -A app.celery_app worker -Q ${1} --without-heartbeat --without-mingle --without-gossip
