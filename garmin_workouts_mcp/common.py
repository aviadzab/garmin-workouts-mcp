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




def generate_workout_data_prompt_logic(description: str) -> dict:
    return {"prompt": f"""
    You are a fitness coach.
    Given the following workout description, create a structured JSON object that represents the workout.
    The generated JSON should be compatible with the `upload_workout` tool.

    Workout Description:
    {description}

    Requirements:
    - The output must be valid JSON.
    - For pace targets, use decimal minutes per km (e.g., 4:40 min/km = 4.67 minutes per km)
    - For time-based steps, use stepDuration in seconds
    - For distance-based steps, use stepDistance with appropriate distanceUnit
    - Use the following structure for the workout object:
    {{
    "name": "Workout Name",
    "type": "running" | "cycling" | "swimming" | "walking" | "cardio" | "strength",
    "steps": [
        {{
        "stepName": "Step Name",
        "stepDescription": "Description",
        "endConditionType": "time" | "distance",
        "stepDuration": duration_in_seconds,
        "stepDistance": distance_value,
        "distanceUnit": "m" | "km" | "mile",
        "stepType": "warmup" | "cooldown" | "interval" | "recovery" | "rest" | "repeat",
        "target": {{
            "type": "no target" | "pace" | "heart rate" | "power" | "cadence" | "speed",
            "value": [minValue, maxValue] | singleValue,
            "unit": "min_per_km" | "bpm" | "watts" | "zone"
        }},
        "numberOfIterations": number,
        "steps": []
        }}
    ]
    }}

    Examples:
    - For 4:40 min/km pace: "value": 4.67 or "value": [4.5, 4.8]
    - For 160 bpm heart rate: "value": 160 or "value": [150, 170]
    - For zone 2 heart rate: "value": 2 and "unit": "zone"
    - For no target: "type": "no target", "value": null, "unit": null
    """}