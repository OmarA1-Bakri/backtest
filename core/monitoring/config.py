"""Monitoring configuration."""

from typing import Dict, Any
from pydantic import BaseModel


class MonitoringConfig(BaseModel):
    """Monitoring configuration settings."""

    # Prometheus settings
    prometheus_port: int = 9091  # Changed from 9090 to avoid conflict
    prometheus_metrics_path: str = "/metrics"
    prometheus_collection_interval: int = 15  # seconds

    # Alert settings
    alert_cooldown_minutes: int = 15
    alert_retention_days: int = 7
    alert_notification_channels: list = ["slack"]

    # Performance monitoring
    slow_operation_threshold_ms: int = 1000
    performance_metrics_retention_days: int = 30

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_retention_days: int = 30

    # ELK stack settings
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    kibana_host: str = "localhost"
    kibana_port: int = 5601
    logstash_host: str = "localhost"
    logstash_port: int = 5044

    # Health check settings
    health_check_interval: int = 60  # seconds
    health_check_timeout: int = 5  # seconds
    health_check_retries: int = 3

    class Config:
        """Pydantic config."""

        env_prefix = "MONITOR_"
        case_sensitive = False


# Global instance
config = MonitoringConfig()
