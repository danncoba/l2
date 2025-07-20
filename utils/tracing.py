from fastapi import Request
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace id to response headers"""

    async def dispatch(self, request: Request, call_next):
        span = trace.get_current_span()
        span_context = span.get_span_context()

        trace_id = None
        if span_context.is_valid:
            trace_id = hex(span_context.trace_id)[2:]

        response = await call_next(request)
        if trace_id:
            response.headers["Morpheus-Trace-Id"] = trace_id

        return response
