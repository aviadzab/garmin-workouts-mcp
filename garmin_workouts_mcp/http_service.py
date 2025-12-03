import garth
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import datetime

from garmin_workouts_mcp.common import CALENDAR_WEEK_ENDPOINT, login, GET_WORKOUT_ENDPOINT

fastapi_app = FastAPI()
login()


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

