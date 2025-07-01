# Configure resource
import logging

from opentelemetry import trace, _logs as logs
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource.create(
    {
        "service.name": "htec-morpheus",
        "service.version": "1.0.0",
        "deployment.environment": "development",
    }
)

# Set up logging
logger_provider = LoggerProvider(resource=resource)

# OTLP Log Exporter
otlp_log_exporter = OTLPLogExporter(endpoint="http://localhost:4317", insecure=True)

# Add log processor
logs.set_logger_provider(logger_provider)
log_processor = BatchLogRecordProcessor(otlp_log_exporter)
logger_provider.add_log_record_processor(log_processor)

# Set up Python logging to use OpenTelemetry
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG)
set_logger_provider(logger_provider)

logger = logging.getLogger(__name__)
logger.info("Something happening")
