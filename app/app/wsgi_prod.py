import os

from django.core.wsgi import get_wsgi_application
from gevent import monkey
from whitenoise import WhiteNoise


# ddtrace.patch_all()
# ddtrace.patch(gevent=True)

# ddtrace.Pin.override(django, tracer=tracer)
# ddtrace.Pin.override(psycopg2, tracer=tracer)
# ddtrace.Pin.override(redis, tracer=tracer)

# monkey.patch_all()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()
application = WhiteNoise(application)
application.add_files("/app/static", prefix="static/")  # type: ignore
