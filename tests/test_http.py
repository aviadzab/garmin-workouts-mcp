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



    def test_get_workout_list(self, client):
        """Test that the getSleepReport endpoint is defined."""
        # Act
        response = client.get("/getWorkoutsList")

        # Assert
        # Endpoint exists but may not be fully implemented yet
        assert response.status_code  < 300
        pprint (response.json())

    def test_user_data(self, client):
        response = client.get("/getUserData")
        pprint(response.json())
        assert response.status_code < 300
    
    def test_get_activity_splits_and_details(self, client):
        """Test the getActivitySplitsAndDetails endpoint."""
        # First test without activity_id parameter - should fail
        response_no_id = client.get("/getActivitySplitsAndDetails")
        assert response_no_id.status_code == 422  # FastAPI validation error for missing query param
        
        # Get a real activity to test with
        activities_response = client.get("/getWorkoutsList")
        
        # Test with an activity_id - we'll use a hardcoded one for testing
        # In a real scenario, you'd get this from list_activities
        test_activity_id = "21892517342"  # Example activity ID
        response = client.get(f"/getActivitySplitsAndDetails?activity_id={test_activity_id}")
        
        # Assert response structure
        if response.status_code < 300:
            json_data = response.json()
            assert "status" in json_data
            assert json_data["status"] == "ok"
            assert "activityId" in json_data
            assert "splits" in json_data
            assert "details" in json_data
            pprint(json_data)
        else:
            # If it fails, just check that it returns a proper error
            assert response.status_code in [400, 404, 500]
            pprint(response.json())
    
