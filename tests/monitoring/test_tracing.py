import pytest
from unittest.mock import Mock, patch
from opentelemetry.trace import SpanKind, Status, StatusCode
from flask import Flask
from celery import Celery
from monitoring.tracing import TracingConfig


@pytest.fixture
def tracing_config():
    return TracingConfig(
        service_name="test-service", jaeger_host="localhost", jaeger_port=6831
    )


def test_tracing_initialization(tracing_config):
    with patch("monitoring.tracing.JaegerExporter") as mock_exporter:
        tracing_config.setup_tracing()
        assert mock_exporter.called
        assert tracing_config.tracer is not None


def test_flask_instrumentation(tracing_config):
    app = Flask(__name__)

    with patch("monitoring.tracing.FlaskInstrumentor") as mock_instrumentor:
        tracing_config.setup_tracing()
        tracing_config.instrument_flask(app)
        mock_instrumentor().instrument_app.assert_called_once()


def test_celery_instrumentation(tracing_config):
    celery_app = Celery()

    with patch("monitoring.tracing.CeleryInstrumentor") as mock_instrumentor:
        tracing_config.setup_tracing()
        tracing_config.instrument_celery(celery_app)
        mock_instrumentor().instrument.assert_called_once()


def test_sqlalchemy_instrumentation(tracing_config):
    mock_engine = Mock()

    with patch("monitoring.tracing.SQLAlchemyInstrumentor") as mock_instrumentor:
        tracing_config.setup_tracing()
        tracing_config.instrument_sqlalchemy(mock_engine)
        mock_instrumentor().instrument.assert_called_once()


def test_redis_instrumentation(tracing_config):
    with patch("monitoring.tracing.RedisInstrumentor") as mock_instrumentor:
        tracing_config.setup_tracing()
        tracing_config.instrument_redis()
        mock_instrumentor().instrument.assert_called_once()


def test_tracer_not_initialized_error(tracing_config):
    with pytest.raises(RuntimeError):
        _ = tracing_config.tracer
