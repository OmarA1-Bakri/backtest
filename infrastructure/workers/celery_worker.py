from infrastructure.celery_config import celery_app
from infrastructure.tasks import run_optimization  # Import tasks to register them

if __name__ == "__main__":
    celery_app.worker_main(
        ["worker", "--loglevel=INFO", "-Q", "optimization,data_processing"]
    )
