"""Script to start all monitoring services."""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

from core.monitoring.config import config
from core.monitoring.metrics import prometheus_exporter
from core.monitoring.alerts import alert_manager
from core.monitoring.health import SystemHealthCheck
from logger import logger


async def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        filename=f"logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(logging.Formatter(config.log_format))

    # Add handler to root logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(config.log_level)

    logger.info("Logging setup completed")


async def monitor_system_health():
    """Periodically check system health."""
    while True:
        try:
            health = await SystemHealthCheck.get_full_health_status()
            if health["status"] != "healthy":
                logger.warning(f"System health degraded: {health}")

            # Check for alerts
            alerts = await alert_manager.check_thresholds()
            if alerts:
                logger.warning(f"New alerts detected: {len(alerts)}")

        except Exception as e:
            logger.error(f"Error in health monitoring: {str(e)}")

        await asyncio.sleep(config.health_check_interval)


async def collect_metrics():
    """Periodically collect and update metrics."""
    while True:
        try:
            await prometheus_exporter.collect_metrics()
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")

        await asyncio.sleep(config.prometheus_collection_interval)


async def start_monitoring():
    """Start all monitoring services."""
    try:
        # Set up logging
        await setup_logging()
        logger.info("Starting monitoring services...")

        # Start Prometheus exporter
        prometheus_exporter.start()

        # Start background tasks
        tasks = [
            asyncio.create_task(monitor_system_health()),
            asyncio.create_task(collect_metrics()),
        ]

        # Wait for all tasks
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Error starting monitoring services: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(start_monitoring())
