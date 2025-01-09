from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from flask import Flask
from celery import Celery
import logging

logger = logging.getLogger(__name__)


class TracingConfig:
    def __init__(
        self, service_name: str, jaeger_host: str = "localhost", jaeger_port: int = 6831
    ):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self._tracer: Optional[trace.Tracer] = None

    def setup_tracing(self) -> None:
        """Initialize OpenTelemetry tracing with Jaeger exporter"""
        try:
            # Create and set TracerProvider
            provider = TracerProvider()
            processor = BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=self.jaeger_host,
                    agent_port=self.jaeger_port,
                )
            )
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

            # Get tracer
            self._tracer = trace.get_tracer(self.service_name)

            logger.info(
                "Tracing initialized successfully",
                extra={
                    "service": self.service_name,
                    "jaeger_host": self.jaeger_host,
                    "jaeger_port": self.jaeger_port,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to initialize tracing",
                extra={"error": str(e), "service": self.service_name},
            )
            raise

    def instrument_flask(self, app: Flask) -> None:
        """Instrument Flask application with OpenTelemetry"""
        FlaskInstrumentor().instrument_app(
            app,
            tracer_provider=trace.get_tracer_provider(),
        )

    def instrument_celery(self, celery_app: Celery) -> None:
        """Instrument Celery with OpenTelemetry"""
        CeleryInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )

    def instrument_sqlalchemy(self, engine) -> None:
        """Instrument SQLAlchemy with OpenTelemetry"""
        SQLAlchemyInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(), engine=engine
        )

    def instrument_redis(self) -> None:
        """Instrument Redis with OpenTelemetry"""
        RedisInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )

    @property
    def tracer(self) -> trace.Tracer:
        """Get the configured tracer"""
        if self._tracer is None:
            raise RuntimeError("Tracer not initialized. Call setup_tracing() first.")
        return self._tracer
