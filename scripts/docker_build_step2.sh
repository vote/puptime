#!/bin/bash

export SECRET_KEY=abcd
python /app/manage.py collectstatic --noinput

# Save space by deleting unnecessary content
rm -rf /root/.cache
