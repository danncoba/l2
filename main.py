import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from routers.configs import config_router
from routers.grades import grades_router
from routers.matrix import matrix_router
from routers.matrix_chats import matrix_chats_router
from routers.notifications import notifications_router
from routers.profile import profile_router
from routers.skills import skills_router
from routers.users import users_router

# Configure resource
resource = Resource.create(
    {
        "service.name": "htec-morpheus",
        "service.version": "1.0.0",
        "deployment.environment": "development",
    }
)

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_trace_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)

# Add span processor
span_processor = BatchSpanProcessor(otlp_trace_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Set up logging
logger_provider = LoggerProvider(resource=resource)

# OTLP Log Exporter
otlp_log_exporter = OTLPLogExporter(endpoint="http://localhost:4317", insecure=True)

# Add log processor
log_processor = BatchLogRecordProcessor(otlp_log_exporter)
logger_provider.add_log_record_processor(log_processor)

# Set up Python logging to use OpenTelemetry
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
set_logger_provider(logger_provider)

logger = logging.getLogger(__name__)

logger.info("This log message will be sent via OpenTelemetry!")
logger.warning("Another log message with a warning level.")

app = FastAPI(
    title="Morpheus @ HTEC",
    description="""Morpheus @ HTEC helps engineers populate and validate their skill matrix.
        Application will remind the engineers, that still have not populated entire matrix, or have some
        unpopulated fields to populate these fields accordingly.
        """,
)

origins = [
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(users_router)
app.include_router(grades_router)
app.include_router(notifications_router)
app.include_router(config_router)
app.include_router(skills_router)
app.include_router(matrix_router)
app.include_router(matrix_chats_router)
