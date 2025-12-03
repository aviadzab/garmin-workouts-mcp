import os
import sys
import logging
import garth

LIST_WORKOUTS_ENDPOINT = "/workout-service/workouts"
GET_WORKOUT_ENDPOINT = "/workout-service/workout/{workout_id}"
GET_ACTIVITY_ENDPOINT = "/activity-service/activity/{activity_id}"
GET_ACTIVITY_WEATHER_ENDPOINT = "/activity-service/activity/{activity_id}/weather"
GET_ACTIVITY_SPLITS_ENDPOINT = "activity-service/activity/{activity_id}/splits"
GET_ACTIVITY_DETAILS_ENDPOINT = "activity-service/activity/{activity_id}/details"
LIST_ACTIVITIES_ENDPOINT = "/activitylist-service/activities/search/activities"
CREATE_WORKOUT_ENDPOINT = "/workout-service/workout"
SCHEDULE_WORKOUT_ENDPOINT = "/workout-service/schedule/{workout_id}"
CALENDAR_WEEK_ENDPOINT = "/calendar-service/year/{year}/month/{month}/day/{day}/start/{start}"
CALENDAR_MONTH_ENDPOINT = "/calendar-service/year/{year}/month/{month}"


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)


def login():
    """Login to Garmin Connect."""
    garth_home = os.environ.get("GARTH_HOME", "~/.garth")
    try:
        garth.resume(garth_home)
    except Exception:
        email = os.environ.get("GARMIN_EMAIL")
        password = os.environ.get("GARMIN_PASSWORD")

        if not email or not password:
            raise ValueError("Garmin email and password must be provided via environment variables (GARMIN_EMAIL, GARMIN_PASSWORD).")

        try:
            garth.login(email, password)
        except Exception as e:
            logger.error("Login failed: %s", e)
            sys.exit(1)

        # Save credentials for future use
        garth.save(garth_home)
