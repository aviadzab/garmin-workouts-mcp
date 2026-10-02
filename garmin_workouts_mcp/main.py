import threading

from fastmcp import FastMCP
import garth
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional

from garmin_workouts_mcp.common import (
    LIST_WORKOUTS_ENDPOINT,
    GET_WORKOUT_ENDPOINT,
    GET_ACTIVITY_ENDPOINT,
    GET_ACTIVITY_SPLITS_ENDPOINT,
    LIST_ACTIVITIES_ENDPOINT,
    SCHEDULE_WORKOUT_ENDPOINT,
    CALENDAR_WEEK_ENDPOINT,
    CALENDAR_MONTH_ENDPOINT,
    GET_ACTIVITY_WEATHER_ENDPOINT,
    logger, login, generate_workout_data_prompt_logic)
from .garmin_workout import make_payload


mcp = FastMCP(name="GarminConnectWorkoutsServer")

# Pydantic input models - ignore extra fields from n8n
class GetActivityInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    activity_id: str


class ListActivitiesInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    limit: int = 20
    start: int = 0
    activityType: Optional[str] = None
    search: Optional[str] = None


class GetCalendarInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    year: int
    month: int
    day: Optional[int] = None
    start: int = 1
    # Allow callers to pass a 'view' or other extra fields; they will be ignored.


@mcp.tool
def list_workouts() -> dict:
    """
    List all workouts available on Garmin Connect.

    Returns:
        A dictionary containing a list of workouts.
    """
    workouts = garth.connectapi(LIST_WORKOUTS_ENDPOINT)
    return {"workouts": workouts}

@mcp.tool
def get_workout(workout_id: str) -> dict:
    """
    Get details of a specific workout by its ID.

    Args:
        workout_id: ID of the workout to retrieve.

    Returns:
        Workout details as a dictionary.
    """
    endpoint = GET_WORKOUT_ENDPOINT.format(workout_id=workout_id)
    workout = garth.connectapi(endpoint)
    return {"workout": workout}

@mcp.tool
def get_activity(input: Any) -> dict:
    """
    Get details of a specific activity by its ID. An activity represents a completed run, ride, swim, etc.

    Args:
        input: either a GetActivityInput instance or a dict with at least `activity_id` (extra fields ignored)

    Returns:
        Activity details as a dictionary.
    """
    # coerce dicts/other mappings into the Pydantic model to ignore extras
    if isinstance(input, dict):
        input = GetActivityInput.model_validate(input)
    elif not isinstance(input, GetActivityInput):
        # allow raw values too (e.g., direct activity_id string)
        try:
            input = GetActivityInput.model_validate(input)
        except Exception:
            # fallback: assume input is activity_id
            input = GetActivityInput.model_validate({"activity_id": input})

    endpoint = GET_ACTIVITY_ENDPOINT.format(activity_id=input.activity_id)
    activity = garth.connectapi(endpoint)
    return activity

@mcp.tool
def list_activities(input: Any) -> dict:
    """
    List activities (completed runs, rides, swims, etc.) from Garmin Connect.

    Args:
        input: either a ListActivitiesInput instance or a dict (extra fields ignored). Contains:
            - limit, start, activityType, search

    Returns:
        A dictionary containing a list of activities and pagination info.
    """
    # coerce dicts/other mappings into the Pydantic model to ignore extras
    if isinstance(input, dict):
        input = ListActivitiesInput.model_validate(input)
    elif not isinstance(input, ListActivitiesInput):
        input = ListActivitiesInput.model_validate(input)

    params: Dict[str, Any] = {"limit": input.limit, "start": input.start}
    if input.activityType is not None:
        params["activityType"] = input.activityType
    if input.search is not None:
        params["search"] = input.search

    activities = garth.connectapi(LIST_ACTIVITIES_ENDPOINT, "GET", params=params)
    return {"activities": activities}

@mcp.tool
def get_activity_splits(activity_id: str) -> dict:
    """
    Get lap/split data for a specific activity.

    Args:
        activity_id: ID of the activity to retrieve splits for.

    Returns:
        activity splits details as a dictionary containing splits data
    """
    endpoint = GET_ACTIVITY_SPLITS_ENDPOINT.format(activity_id=activity_id)
    splits = garth.connectapi(endpoint)
    return splits

@mcp.tool
def get_activity_weather(activity_id: str) -> dict:
    """
    Get weather information for a specific activity.

    Args:
        activity_id: ID of the activity to retrieve weather for.

    Returns:
        Weather details as a dictionary containing temperature, conditions, etc.
    """
    endpoint = GET_ACTIVITY_WEATHER_ENDPOINT.format(activity_id=activity_id)
    weather = garth.connectapi(endpoint)
    return weather

@mcp.tool
def schedule_workout(workout_id: str, date: str) -> dict:
    """
    Schedule a workout on Garmin Connect.

    Args:
        workout_id: ID of the workout to schedule.
        date: Date to schedule the workout in ISO format (YYYY-MM-DD).

    Returns:
        workoutScheduleId: ID of the scheduled workout.

    Raises:
        ValueError: If the date format is incorrect.
        Exception: If scheduling the workout fails.
    """

    # verify date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in ISO format (YYYY-MM-DD)")

    payload = {
        "date": date,
    }

    endpoint = SCHEDULE_WORKOUT_ENDPOINT.format(workout_id=workout_id)
    result = garth.connectapi(endpoint, method="POST", json=payload)
    workout_scheduled_id = result.get("workoutScheduleId")
    if workout_scheduled_id is None:
        raise Exception(f"Scheduling workout failed: {result}")

    return {"workoutScheduleId": str(workout_scheduled_id)}

@mcp.tool
def delete_workout(workout_id: str) -> bool:
    """
    Delete a workout from Garmin Connect.

    Args:
        workout_id: ID of the workout to delete.

    Returns:
        True if the deletion was successful, False otherwise.
    """
    endpoint = GET_WORKOUT_ENDPOINT.format(workout_id=workout_id)

    try:
        garth.connectapi(endpoint, method="DELETE")
        logger.info("Workout %s deleted successfully", workout_id)
        return True
    except Exception as e:
        logger.error("Failed to delete workout %s: %s", workout_id, e)
        return False

@mcp.tool
def upload_workout(workout_data: dict) -> dict:
    """
    Uploads a structured workout to Garmin Connect.

    Args:
        workout_data: Workout data in JSON format to upload. Use the `generate_workout_data_prompt` tool to create a prompt for the LLM to generate this data.

    Returns:
        The uploaded workout's ID on Garmin Connect.

    Raises:
        Exception: If the upload fails or the workout ID is not returned.
    """

    logger.info("Workout data received from client: %s", workout_data)

    try:
        # Convert to Garmin payload format
        payload = make_payload(workout_data)

        # logging the payload for debugging
        logger.info("Payload to be sent to Garmin Connect: %s", payload)

        # Create workout on Garmin Connect
        result = garth.connectapi("/workout-service/workout", method="POST", json=payload)

        # logging the result for debugging
        logger.info("Response from Garmin Connect: %s", result)

        workout_id = result.get("workoutId")

        if workout_id is None:
            raise Exception("No workout ID returned")

        return {"workoutId": str(workout_id)}

    except Exception as e:
        raise Exception(f"Failed to upload workout to Garmin Connect: {str(e)}")

@mcp.tool
def get_calendar(input: Any) -> dict:
    """
    Get calendar data from Garmin Connect for different time periods.

    Args:
        input: GetCalendarInput or dict with fields `year`, `month`, optional `day` and `start`.
               Extra fields are ignored.

    Returns:
        Calendar data with workouts and activities for the specified period.

    Raises:
        ValueError: If any of the date parameters are invalid.
    """
    # coerce dicts/other mappings into the Pydantic model to ignore extras
    if isinstance(input, dict):
        input = GetCalendarInput.model_validate(input)
    elif not isinstance(input, GetCalendarInput):
        input = GetCalendarInput.model_validate(input)

    # Input validation (same checks as before)
    if not (1900 <= input.year <= 2100):
        raise ValueError(f"Year must be between 1900 and 2100, got {input.year}")

    if not (1 <= input.month <= 12):
        raise ValueError(f"Month must be between 1 and 12, got {input.month}")

    if input.day is not None:
        if not (1 <= input.day <= 31):
            raise ValueError(f"Day must be between 1 and 31, got {input.day}")

    # Convert month from 1-based (human readable) to 0-based (Garmin API)
    garmin_month = input.month - 1

    if input.day is not None:
        # Weekly view
        endpoint = CALENDAR_WEEK_ENDPOINT.format(
            year=input.year, month=garmin_month, day=input.day, start=input.start
        )
        view_type = "week"
    else:
        # Monthly view (default)
        endpoint = CALENDAR_MONTH_ENDPOINT.format(
            year=input.year, month=garmin_month
        )
        view_type = "month"

    calendar_data = garth.connectapi(endpoint)

    return {
        "calendar": calendar_data,
        "view_type": view_type,
        "period": {
            "year": input.year,
            "month": input.month,
            "day": input.day,
            "start": input.start if input.day else None,
        }
    }

@mcp.tool
def generate_workout_data_prompt(description: str) -> dict:
    """
    Generate prompt for LLM to create structured workout data based on a natural language description. The LLM
    should use the returned prompt to generate a JSON object that can then be used with the `upload_workout` tool.

    Args:
        description: Natural language description of the workout

    Returns:
        Prompt for the LLM to generate structured workout data
    """

    return generate_workout_data_prompt_logic(description)

@mcp.tool
def daily_body_battery(end_date: date | None = None, days: int = 1) -> str | list[garth.DailyBodyBatteryStress]:
    """
    Get daily body battery data for a given date and number of days.
    
    Args:
        end_date: the last day to receive the information for (until date), default current date
        days: number of days to get the daily body battery information, default 1

    Returns:
        daily body battery information
    """
    return garth.DailyBodyBatteryStress.list(end_date, days)

@mcp.tool
def daily_hrv(end_date: date | None = None, days: int = 1) -> str | list[garth.DailyHRV]:
    """
    Get daily heart rate variability data for a given date and number of days.
    
    Args:
        end_date: the last day to receive the information for (until date), default current date
        days: number of days to get the daily heart rate variability information, default 1

    Returns:
        daily heart rate variability data
    """
    return garth.DailyHRV.list(end_date, days)
    

@mcp.tool
def hrv_data(end_date: date | None = None, days: int = 1) -> str | list[garth.HRVData]:
    """
    Get detailed HRV data for a given date and number of days.
    
    Args:
        end_date: the last day to receive the information for (until date), default current date
        days: number of days to get the detailed heart rate variability information, default 1

    Returns:
        detailed heart rate variability data
    """
    return garth.HRVData.list(end_date, days)

@mcp.tool

def daily_sleep(end_date: date | None = None, days: int = 1) -> str | list[garth.DailySleep]:
    """
    Get daily sleep summary data for a given date and number of days.
    
    Args:
        end_date: the last day to receive the information for (until date), default current date
        days: number of days to get daily sleep summary information, default 1

    Returns:
        daily sleep summary data
    """
    return garth.DailySleep.list(end_date, days)

@mcp.tool    
def nightly_sleep(
    end_date: date | None = None, nights: int = 1, sleep_movement: bool = False
) -> str | list[garth.SleepData]:
    """
    Get sleep stats for a given date and number of nights.
    If no nights are provided, 1 night will be used.
    sleep_movement provides detailed sleep movement data. If looking at
    multiple nights, it'll be a lot of data.
    Args:
        end_date: the last day to receive the information for (until date), default current date
        nights: number of nights to get the detailed sleep information, default 1
        sleep_movement: whether to provide detailed sleep movement data (may contain a lot of data if used for many nights)
    Returns:
        detailed sleep stats data
    """
    sleep_data = garth.SleepData.list(end_date, nights)
    if not sleep_movement:
        for night in sleep_data:
            if hasattr(night, "sleep_movement"):
                del night.sleep_movement
    return sleep_data


def main():
    """Main entry point for the console script."""
    logger.info("logging in to garmin using garth...")
    login()

    # Start FastAPI health check service in a separate thread
    logger.info("Starting FastAPI health service on port 3334...")
    def run_fastapi():
        import uvicorn
        from garmin_workouts_mcp.http_service import fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=3334, log_level="info")

    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()

    logger.info("mcp ")
    logger.info("Starting Garmin Connect Workouts Server version 0.6.1 ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=3333, path="/mcp")


if __name__ == "__main__":
    main()
