from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import httpx
import json
from dotenv import load_dotenv
from os import getenv

load_dotenv()

DIALECT="mobile" # TODO: try "otp" dialect?
STOP_ID="BKK_F02772" # Ond vezér útja / Szentmihályi út (dél felé)
KEY=getenv("BKK_API_KEY")

EXTERNAL_API_URL = f"https://futar.bkk.hu/api/query/v1/ws/{DIALECT}/api/where/arrivals-and-departures-for-stop?key={KEY}&stopId={STOP_ID}&includeReferences=false&stopTimeType=DEPARTURE&limit=5"

app = FastAPI()

@app.get("/data")
async def fetch_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(EXTERNAL_API_URL)
        if response.is_error:
            return []
        data = response.json()
        current_time = round(int(data["currentTime"]) / 1000)
        stop_times = data["data"]["entry"]["stopTimes"]
        departures = []
        for item in stop_times:
            t = item.get("predictedDepartureTime") or item.get("departureTime")
            if t:
                departures.append(round((int(t) - current_time) / 60))
        return departures

app.mount("/", StaticFiles(directory="static", html=True), name="static")