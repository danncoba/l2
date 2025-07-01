import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib import URLLibInstrumentor


def setup_telemetry():
    """Setup OpenTelemetry tracing and instrumentation"""

    # Create a resource to identify your service
    resource = Resource.create(
        {
            "service.name": "htec-morpheus",
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create TracerProvider
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter to send traces to the collector
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    # Add BatchSpanProcessor to the TracerProvider
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set the TracerProvider as the global default
    trace.set_tracer_provider(tracer_provider)

    # Instrument various libraries
    try:
        PsycopgInstrumentor().instrument()
    except Exception as e:
        print(f"Failed to instrument psycopg: {e}")

    try:
        RedisInstrumentor().instrument()
    except Exception as e:
        print(f"Failed to instrument redis: {e}")

    try:
        RequestsInstrumentor().instrument()
    except Exception as e:
        print(f"Failed to instrument requests: {e}")

    try:
        URLLibInstrumentor().instrument()
    except Exception as e:
        print(f"Failed to instrument urllib: {e}")

    return tracer_provider


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry"""
    FastAPIInstrumentor.instrument_app(app)
    return app
