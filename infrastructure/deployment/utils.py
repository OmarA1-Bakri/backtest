import os
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
import requests
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Deployment Metrics
DEPLOYMENT_STATUS = Gauge(
    "deployment_status",
    "Current deployment status (1=success, 0=failed)",
    ["environment", "version"],
)

DEPLOYMENT_DURATION = Gauge(
    "deployment_duration_seconds",
    "Time taken for deployment",
    ["environment", "version"],
)

ROLLBACK_COUNT = Counter(
    "deployment_rollbacks_total",
    "Number of deployment rollbacks",
    ["environment", "reason"],
)


@dataclass
class DeploymentState:
    version: str
    timestamp: datetime
    status: str  # 'success' or 'failed'
    environment: str
    commit_hash: str
    artifacts: Dict[str, str]


class DeploymentManager:
    def __init__(
        self,
        environment: str,
        state_file: str = "deployment_state.json",
        health_check_url: str = "http://localhost:5000/health",
    ):
        self.environment = environment
        self.state_file = state_file
        self.health_check_url = health_check_url
        self._current_state: Optional[DeploymentState] = None
        self._load_state()

    def _load_state(self) -> None:
        """Load deployment state from file"""
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self._current_state = DeploymentState(
                    version=data["version"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    status=data["status"],
                    environment=data["environment"],
                    commit_hash=data["commit_hash"],
                    artifacts=data["artifacts"],
                )

    def _save_state(self) -> None:
        """Save deployment state to file"""
        if self._current_state:
            with open(self.state_file, "w") as f:
                json.dump(
                    {
                        "version": self._current_state.version,
                        "timestamp": self._current_state.timestamp.isoformat(),
                        "status": self._current_state.status,
                        "environment": self._current_state.environment,
                        "commit_hash": self._current_state.commit_hash,
                        "artifacts": self._current_state.artifacts,
                    },
                    f,
                    indent=2,
                )

    def perform_health_check(self) -> bool:
        """Check if the application is healthy"""
        try:
            response = requests.get(self.health_check_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def deploy(self, version: str, commit_hash: str, artifacts: Dict[str, str]) -> bool:
        """Deploy a new version"""
        try:
            # Store previous state for potential rollback
            previous_state = self._current_state

            # Update state with new deployment
            self._current_state = DeploymentState(
                version=version,
                timestamp=datetime.utcnow(),
                status="pending",
                environment=self.environment,
                commit_hash=commit_hash,
                artifacts=artifacts,
            )

            # Perform deployment steps
            self._deploy_artifacts(artifacts)

            # Verify deployment
            if self.perform_health_check():
                self._current_state.status = "success"
                self._save_state()
                DEPLOYMENT_STATUS.labels(
                    environment=self.environment, version=version
                ).set(1)
                return True
            else:
                # Deployment failed, rollback
                logger.error(f"Deployment of version {version} failed health check")
                if previous_state:
                    self.rollback(previous_state, reason="health_check_failed")
                return False

        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            DEPLOYMENT_STATUS.labels(environment=self.environment, version=version).set(
                0
            )
            return False

    def _deploy_artifacts(self, artifacts: Dict[str, str]) -> None:
        """Deploy artifacts to their respective locations"""
        for artifact_type, path in artifacts.items():
            if artifact_type == "backend":
                # Deploy backend service
                subprocess.run(["docker-compose", "up", "-d", "backend"])
            elif artifact_type == "frontend":
                # Deploy frontend assets
                subprocess.run(["docker-compose", "up", "-d", "frontend"])

    def rollback(self, target_state: DeploymentState, reason: str = "manual") -> bool:
        """Rollback to a previous state"""
        try:
            logger.info(f"Rolling back to version {target_state.version}")

            # Perform rollback
            self._deploy_artifacts(target_state.artifacts)

            if self.perform_health_check():
                self._current_state = target_state
                self._save_state()

                # Record rollback metrics
                ROLLBACK_COUNT.labels(environment=self.environment, reason=reason).inc()

                logger.info(f"Successfully rolled back to {target_state.version}")
                return True
            else:
                logger.error("Rollback failed health check")
                return False

        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False


class BlueGreenDeployment:
    def __init__(self, environment: str, blue_port: int = 5000, green_port: int = 5001):
        self.environment = environment
        self.blue_port = blue_port
        self.green_port = green_port
        self.active_color = self._get_active_color()

    def _get_active_color(self) -> str:
        """Determine which environment is currently active"""
        try:
            with open("active_environment.txt", "r") as f:
                return f.read().strip() or "blue"
        except FileNotFoundError:
            return "blue"

    def _save_active_color(self, color: str) -> None:
        """Save the currently active environment"""
        with open("active_environment.txt", "w") as f:
            f.write(color)

    def deploy(self, version: str, artifacts: Dict[str, str]) -> bool:
        """Perform a blue-green deployment"""
        target_color = "green" if self.active_color == "blue" else "blue"
        target_port = self.green_port if target_color == "green" else self.blue_port

        try:
            # Deploy to inactive environment
            deployment_manager = DeploymentManager(
                f"{self.environment}-{target_color}",
                health_check_url=f"http://localhost:{target_port}/health",
            )

            if deployment_manager.deploy(version, artifacts):
                # Switch traffic to new environment
                self.active_color = target_color
                self._save_active_color(target_color)
                logger.info(f"Switched traffic to {target_color} environment")
                return True
            else:
                logger.error("Deployment to new environment failed")
                return False

        except Exception as e:
            logger.error(f"Blue-green deployment failed: {str(e)}")
            return False

    def rollback(self) -> bool:
        """Rollback to the previous environment"""
        previous_color = "blue" if self.active_color == "green" else "green"
        previous_port = self.blue_port if previous_color == "blue" else self.green_port

        try:
            # Verify previous environment is healthy
            deployment_manager = DeploymentManager(
                f"{self.environment}-{previous_color}",
                health_check_url=f"http://localhost:{previous_port}/health",
            )

            if deployment_manager.perform_health_check():
                # Switch back to previous environment
                self.active_color = previous_color
                self._save_active_color(previous_color)
                logger.info(f"Rolled back to {previous_color} environment")
                return True
            else:
                logger.error("Previous environment is not healthy")
                return False

        except Exception as e:
            logger.error(f"Blue-green rollback failed: {str(e)}")
            return False
