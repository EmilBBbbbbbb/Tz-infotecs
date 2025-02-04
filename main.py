import uvicorn
from fastapi import FastAPI
import openmeteo_requests
from sqlalchemy.ext.asyncio import create_async_engine, async_session

import requests_cache
import pandas as pd
from retry_requests import retry

# Set up the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
open_meteo = openmeteo_requests.Client(session=retry_session)

url = "https://api.open-meteo.com/v1/forecast"

engine = create_async_engine('sqlite+aiosqlite:///weather.db')

app = FastAPI()


@app.get('/weather/current')
def get_weather_now(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "surface_pressure", "wind_speed_10m"],
        "forecast_days": 1
    }
    responses = open_meteo.weather_api(url, params=params)
    response = responses[0]

    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_surface_pressure = current.Variables(1).Value()
    current_wind_speed_10m = current.Variables(2).Value()

    return {"Current temperature_2m": current_temperature_2m,
            "Current surface_pressure": current_surface_pressure,
            "Current wind_speed_10m": current_wind_speed_10m}


if __name__ == "__main__":
    uvicorn.run('main:app', reload=True)
