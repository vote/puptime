#!/bin/bash

gunicorn -b 0.0.0.0:8000 -c /app/app/gunicorn.conf.py app.wsgi_prod
