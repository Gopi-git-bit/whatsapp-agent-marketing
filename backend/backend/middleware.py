"""
Custom middleware for monitoring request latency.

This middleware measures the time taken to process each HTTP request and
compares it against a configurable threshold (`SLA_THRESHOLD_SECONDS`).  If
the processing time exceeds the threshold, the middleware logs a warning
message.  The elapsed time is also injected into a custom HTTP response
header (`X-Response-Time`) so that clients (and Sentry) can record timing
information.
"""
from __future__ import annotations

import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SLAMiddleware:
    """Measure and log request durations for simple SLA monitoring."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        elapsed = time.monotonic() - start

        # Add the response time to a custom header in milliseconds
        response['X-Response-Time'] = f'{elapsed * 1000:.2f} ms'

        # If the request took longer than the configured SLA threshold, log a warning
        threshold = getattr(settings, 'SLA_THRESHOLD_SECONDS', 0.5)
        if elapsed > threshold:
            logger.warning(
                "Request to %s took %.2f s which exceeds the SLA threshold of %.2f s",
                request.path,
                elapsed,
                threshold,
            )
        return response