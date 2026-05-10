from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import httpx
import json
from dotenv import load_dotenv
from os import getenv

load_dotenv()

DIALECT="mobile" # TODO: try "otp" dialect?
KEY=getenv("BKK_API_KEY")
URL_BASE = f"https://futar.bkk.hu/api/query/v1/ws/mobile/api/where/arrivals-and-departures-for-stop?key={KEY}&includeReferences=false&stopTimeType=DEPARTURE&limit=5"

STOP_ID_80="BKK_F02772" # Ond vezér útja / Szentmihályi út (dél felé)
STOP_ID_H8="BKK_19798281" # Rákosfalva
STOP_ID_45="BKK_F01791" # Rákosfalva H. Note: itt van egy "volan" is.

URL_80=f"&stopId={STOP_ID_80}"
URL_H8=f"&stopId={STOP_ID_H8}"
URL_45=f"&stopId={STOP_ID_45}" # TODO: valamiert nem kuld el csak egy departuret


app = FastAPI()

@app.get("/data")
async def fetch_external_data():
    departures={"80":[], "H8":[], "45":[]}
    async with httpx.AsyncClient() as client:
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
                if item.get("stopHeadsign") == "Örs Vezér Tere": # TODO check the spelling here
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")
