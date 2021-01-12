#!/bin/bash

celery inspect ping -A app.celery_app -d celery@$HOSTNAME
