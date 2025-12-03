from pathlib import Path
from pprint import pprint

import pytest
import os
from dotenv import load_dotenv


# Load .env file from the parent directory
env_path = Path(__file__).parent.parent.parent.joinpath('.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Try loading from current directory
    load_dotenv()
os.environ["GARMIN_EMAIL"] = os.environ.get("LE_EMAIL")
from fastapi.testclient import TestClient
from garmin_workouts_mcp.http_service import fastapi_app


class TestServiceEndpoint:
    """Test cases for the /health endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(fastapi_app)

    def test_health_endpoint_success(self, client):
        """Test that the health endpoint returns 200 OK with correct status."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


    def test_today_workout_endpoint(self, client):
        """Test that the getTodayWorkout endpoint is defined."""
        # Act
        response = client.get("/getTodayWorkout")

        # Assert
        # Endpoint exists but may not be fully implemented yet
        assert response.status_code  < 300
        pprint (response.json())

    def test_sleep_report_endpoint(self, client):
        """Test that the getSleepReport endpoint is defined."""
        # Act
        response = client.get("/getSleepReport")

        # Assert
        # Endpoint exists but may not be fully implemented yet
        assert response.status_code  < 300
        pprint (response.json())

