import logging

import ddtrace.filters
from ddtrace.tracer import Tracer
from django.conf import settings

logger = logging.getLogger("apm")

# Return before writing to DataDog for now instead of removing
# the code so we can reactivate it easily later when needed.

class UptimeTracer(Tracer):
    def write(self, spans):
        logger.debug(spans)
        # if settings.DEBUG:
        return # return to under If to restore DataDog logging
        return super().write(spans)


tracer = UptimeTracer()
tracer.configure(
    settings={"FILTERS": [ddtrace.filters.FilterRequestsOnUrl(r".+/-/health/$"),],}
)
