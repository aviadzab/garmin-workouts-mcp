import os

import garth
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import datetime

from garminconnect import Garmin

from garmin_workouts_mcp.common import CALENDAR_WEEK_ENDPOINT, login, GET_WORKOUT_ENDPOINT, \
    generate_workout_data_prompt_logic, LIST_WORKOUTS_ENDPOINT, GET_ACTIVITY_SPLITS_ENDPOINT, \
    GET_ACTIVITY_DETAILS_ENDPOINT

fastapi_app = FastAPI()
login()

garmin = Garmin(
    os.getenv("GARMIN_EMAIL"),
    os.getenv("GARMIN_PASSWORD")
)
garmin.login()


def serialize_object(obj):
    """Helper function to serialize objects to dictionaries."""
    d = obj.__dict__
    if "calendar_date" in d and isinstance(d["calendar_date"], datetime.date):
        d["calendar_date"] = d["calendar_date"].strftime("%Y-%m-%d")
    return str(obj)

@fastapi_app.get("/health")
def health():
    return JSONResponse(content={"status": "ok"})


@fastapi_app.get("/getTodayWorkout")
def get_today_workout(week_start: int = 0):
    workouts = []

    today = datetime.date.today()
    endpoint = CALENDAR_WEEK_ENDPOINT.format(
        year=today.year, month=today.month-1, day=today.day, start=week_start
    )
    calendar_data = garth.connectapi(endpoint)
    today_str = today.strftime("%Y-%m-%d")
    items = [it for it in calendar_data.get("calendarItems", [] ) if it.get("date", "") == today_str and it.get("itemType", "") == "workout"]

    if items:
        for it in items:
            endpoint = GET_WORKOUT_ENDPOINT.format(workout_id=it.get("workoutId"))
            workout_data = garth.connectapi(endpoint)
            workouts.append(workout_data)

    return JSONResponse(content={"status": "ok", "numWorkout": len(workouts),"workouts": workouts})


@fastapi_app.get("/getSleepReport")
def get_sleep_report():
    """Placeholder for future sleep report implementation."""
    sleep_data = garth.SleepData.list(None, 1)
    has_sleep = False
    report = {}
    if len(sleep_data) > 0:
        has_sleep = True
        night = sleep_data[0]
        if hasattr(night, "sleep_movement"):
            del night.sleep_movement
        report["sleep"] = serialize_object(night.daily_sleep_dto)

    hrv_data = garth.DailyHRV.list(None, 1)
    if hrv_data:
        has_sleep = True
        report["hrv"] = serialize_object(hrv_data[0])

    return JSONResponse(content={"status": "ok", "hasSleep": has_sleep, "report": report})

@fastapi_app.get("/getGeneratedWorkoutPrompt")
def generate_workout_prompt(description: str):
    return generate_workout_data_prompt_logic(description)


@fastapi_app.get("/getWorkoutsList")
def get_workout_summaries():
    workouts = garth.connectapi(LIST_WORKOUTS_ENDPOINT)
    out_workouts = []
    fields_to_keep = ["workoutId", "workoutName", "description","sportType","estimatedDurationInSecs","estimatedDistanceInMeters"]
    for workout in workouts:
        out_workouts.append( {key: workout[key] for key in fields_to_keep if key in workout})
    return {"workouts": out_workouts}

@fastapi_app.get("/getUserData")
def get_user_data():
    predictor_data = garmin.get_race_predictions()
    return {"user_profile": garth.UserProfile.get(), "user_settings": garth.UserSettings.get()}

@fastapi_app.get("/getActivitySplitsAndDetails")
def get_activity_splits_and_details(activity_id: str):
    """Get splits and details for a specific activity.
    
    Args:
        activity_id: The ID of the activity to retrieve splits and details for.
        
    Returns:
        JSON response containing splits and activity details.
    """
    if not activity_id:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "activity_id parameter is required"}
        )
    
    try:
        # Get activity splits
        splits_endpoint = GET_ACTIVITY_SPLITS_ENDPOINT.format(activity_id=activity_id)
        splits_data = garth.connectapi(splits_endpoint)
        
        # Get activity details
        details_endpoint = GET_ACTIVITY_DETAILS_ENDPOINT.format(activity_id=activity_id)
        details_data = garth.connectapi(details_endpoint)
        
        return JSONResponse(content={
            "status": "ok",
            "activityId": activity_id,
            "splits": splits_data,
            "details": details_data
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


