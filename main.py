from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient
from dotenv import load_dotenv
from os import getenv

load_dotenv()
KEY = getenv("BKK_API_KEY")
BKK_URL_BASE = f"https://futar.bkk.hu/api/query/v1/ws/mobile/api/where/arrivals-and-departures-for-stop?key={KEY}&includeReferences=false&stopTimeType=DEPARTURE"
STOP_ID_80 = "BKK_F02772"
STOP_ID_H8 = "BKK_19798281"
STOP_ID_45 = "BKK_F01791"
URL_80 = f"&stopId={STOP_ID_80}"
URL_H8 = f"&stopId={STOP_ID_H8}"
URL_45 = f"&stopId={STOP_ID_45}"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_PARAMS = {
    "latitude": 47.4984,
    "longitude": 19.0404,
    "daily": "weather_code,apparent_temperature_max,apparent_temperature_min",
    "timezone": "Europe/Berlin",
    "forecast_days": 1,
}

app = FastAPI()


@app.get("/departures")
async def fetch_departures():
    external_data = {"80": [], "H8": [], "45": []}
    async with AsyncClient() as client:
        # --- Bus 80 ---
        response = await client.get(f"{BKK_URL_BASE}{URL_80}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                t = item.get("predictedDepartureTime") or item.get("departureTime")
                departure_time = round((int(t) - current_time) / 60)
                if t and departure_time > 0:
                    external_data["80"].append(departure_time)

        # --- H8 ---
        response = await client.get(f"{BKK_URL_BASE}{URL_H8}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                if item.get("stopHeadsign") == "Örs vezér tere":
                    t = item.get("predictedDepartureTime") or item.get("departureTime")
                    departure_time = round((int(t) - current_time) / 60)
                    if t and departure_time > 0:
                        external_data["H8"].append(departure_time)

        # --- Bus 45 ---
        response = await client.get(f"{BKK_URL_BASE}{URL_45}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                if item.get("stopHeadsign") == "Cinkota, Lassú utca":
                    t = item.get("predictedDepartureTime") or item.get("departureTime")
                    departure_time = round((int(t) - current_time) / 60)
                    if t and departure_time > 0:
                        external_data["45"].append(departure_time)

    return external_data

@app.get("/weather")
async def fetch_weather():
    external_data = {}
    async with AsyncClient() as client:
        response = await client.get(WEATHER_URL, params=WEATHER_PARAMS)
        if not response.is_error:
            data = response.json()
            daily = data.get("daily", {})
            code = daily.get("weather_code", [None])[0]
            external_data = {
                "weather_code": code,
                "apparent_temperature_max": daily.get("apparent_temperature_max", [None])[0],
                "apparent_temperature_min": daily.get("apparent_temperature_min", [None])[0],
            }
    return external_data

app.mount("/icons", StaticFiles(directory="icons"), name="icons")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
