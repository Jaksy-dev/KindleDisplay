from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient
from dotenv import load_dotenv
from os import getenv

load_dotenv()

DIALECT="mobile" # TODO: try "otp" dialect?
KEY=getenv("BKK_API_KEY")
URL_BASE = f"https://futar.bkk.hu/api/query/v1/ws/mobile/api/where/arrivals-and-departures-for-stop?key={KEY}&includeReferences=false&stopTimeType=DEPARTURE"

STOP_ID_80="BKK_F02772" # Ond vezér útja / Szentmihályi út (dél felé)
STOP_ID_H8="BKK_19798281" # Rákosfalva
STOP_ID_45="BKK_F01791" # Rákosfalva H

URL_80=f"&stopId={STOP_ID_80}"
URL_H8=f"&stopId={STOP_ID_H8}"
URL_45=f"&stopId={STOP_ID_45}"


app = FastAPI()

@app.get("/data")
async def fetch_external_data():
    departures={"80":[], "H8":[], "45":[]}
    async with AsyncClient() as client:
        response = await client.get(f"{URL_BASE}{URL_80}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                t = item.get("predictedDepartureTime") or item.get("departureTime")
                departure_time = round((int(t) - current_time) / 60)
                if t and departure_time > 0:
                    departures["80"].append(departure_time)
        # ===========================================
        response = await client.get(f"{URL_BASE}{URL_H8}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                if item.get("stopHeadsign") == "Örs vezér tere":
                    t = item.get("predictedDepartureTime") or item.get("departureTime")
                    departure_time = round((int(t) - current_time) / 60)
                    if t and departure_time > 0:
                        departures["H8"].append(departure_time)
        # ===========================================
        response = await client.get(f"{URL_BASE}{URL_45}")
        if not response.is_error:
            data = response.json()
            current_time = round(int(data["currentTime"]) / 1000)
            stop_times = data["data"]["entry"]["stopTimes"]
            for item in stop_times:
                if item.get("stopHeadsign") == "Cinkota, Lassú utca":
                    t = item.get("predictedDepartureTime") or item.get("departureTime")
                    departure_time = round((int(t) - current_time) / 60)
                    if t and departure_time > 0:
                        departures["45"].append(departure_time)
    return departures



"""
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 47.4984,
	"longitude": 19.0404,
	"daily": ["sunrise", "sunset"],
	"hourly": ["temperature_2m", "rain", "showers", "snowfall", "apparent_temperature", "precipitation_probability"],
	"current": ["temperature_2m", "precipitation", "rain", "showers", "snowfall"],
	"timezone": "Europe/Berlin",
	"forecast_days": 1,
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_precipitation = current.Variables(1).Value()
current_rain = current.Variables(2).Value()
current_showers = current.Variables(3).Value()
current_snowfall = current.Variables(4).Value()

print(f"\nCurrent time: {current.Time()}")
print(f"Current temperature_2m: {current_temperature_2m}")
print(f"Current precipitation: {current_precipitation}")
print(f"Current rain: {current_rain}")
print(f"Current showers: {current_showers}")
print(f"Current snowfall: {current_snowfall}")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_rain = hourly.Variables(1).ValuesAsNumpy()
hourly_showers = hourly.Variables(2).ValuesAsNumpy()
hourly_snowfall = hourly.Variables(3).ValuesAsNumpy()
hourly_apparent_temperature = hourly.Variables(4).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(5).ValuesAsNumpy()

hourly_data = {
	"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	).tz_convert("Europe/Berlin")
}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["rain"] = hourly_rain
hourly_data["showers"] = hourly_showers
hourly_data["snowfall"] = hourly_snowfall
hourly_data["apparent_temperature"] = hourly_apparent_temperature
hourly_data["precipitation_probability"] = hourly_precipitation_probability

hourly_dataframe = pd.DataFrame(data = hourly_data)
print("\nHourly data\n", hourly_dataframe)

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_sunrise = daily.Variables(0).ValuesInt64AsNumpy()
daily_sunset = daily.Variables(1).ValuesInt64AsNumpy()

daily_data = {
	"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	).tz_convert("Europe/Berlin")
}

daily_data["sunrise"] = daily_sunrise
daily_data["sunset"] = daily_sunset

daily_dataframe = pd.DataFrame(data = daily_data)
print("\nDaily data\n", daily_dataframe)


"""

app.mount("/", StaticFiles(directory="static", html=True), name="static")
