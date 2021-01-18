import logging

import ddtrace.filters
from ddtrace.tracer import Tracer
from django.conf import settings

logger = logging.getLogger("apm")


class UptimeTracer(Tracer):
    def write(self, spans):
        logger.debug(spans)
        if settings.DEBUG:
            return
        return super().write(spans)


tracer = UptimeTracer()
tracer.configure(
    settings={
        "FILTERS": [
            ddtrace.filters.FilterRequestsOnUrl(r".+/-/health/$"),
        ],
    }
)
