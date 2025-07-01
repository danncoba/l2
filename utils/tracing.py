from fastapi import Request
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get the current span context
        span = trace.get_current_span()
        span_context = span.get_span_context()

        # Extract the trace ID if the span context is valid
        trace_id = None
        if span_context.is_valid:
            trace_id = hex(span_context.trace_id)[2:]  # Convert to hex string and remove '0x' prefix

        # Process the request and get the response
        response = await call_next(request)

        # Add the trace ID to the response headers if available
        if trace_id:
            response.headers["X-Trace-Id"] = trace_id

        return response