import uvicorn
from fastapi import FastAPI, Depends, Query
import openmeteo_requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import Annotated

import httpx
from datetime import datetime

import numpy as np

from db.engine import create_db, session_maker
from db.models.cities import Cities

import requests_cache
from retry_requests import retry

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройте клиент Open-Meteo API с кешем и повторите попытку в случае ошибки.
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
open_meteo = openmeteo_requests.Client(session=retry_session)

url = "https://api.open-meteo.com/v1/forecast"

app = FastAPI()

scheduler = AsyncIOScheduler()


async def get_session():
    async with session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Функция для получения координат по названию города
async def get_coordinates(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if "results" in data:
        lat = data["results"][0]["latitude"]
        lon = data["results"][0]["longitude"]
        return lat, lon
    return None


# Функция обновления погоды для всех городов
async def update_weather():
    async with session_maker() as session:
        result = await session.execute(select(Cities))
        cities = result.scalars().all()
        for city in cities:
            city_name = city.citiName
            coordinates = await get_coordinates(city_name)
            if coordinates:
                weather = await get_weather_now(coordinates[0], coordinates[1])
                if weather:
                    city.temp = weather['Current temperature_2m']
                    city.speed = weather['Current wind_speed_10m']
                    city.pressure = weather['Current surface_pressure']
                    await session.commit()


# Добавляем задачу обновления каждые 15 минут
scheduler.add_job(update_weather, "interval", minutes=15)


@app.on_event("startup")
async def startup_event():
    scheduler.start()  # Запускаем планировщик


# Функция для создания бд
@app.post('/setup')
async def add_cities():
    await create_db()
    return {
    "message": "Database created successfully"
    }


# Функция для получения данных о погоде по координатам в настоящий момент
@app.get('/weather/current')
async def get_weather_now(latitude: float, longitude: float):
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


# Функция для добавления города в БД
@app.post('/weather/add_citi')
async def add_citi(citi_name: str, session: SessionDep):
    citi_coord = await get_coordinates(citi_name)
    citi_weather = await get_weather_now(citi_coord[0], citi_coord[1])

    new_citi = Cities(
        citiName=citi_name,
        temp=citi_weather['Current temperature_2m'],
        speed=citi_weather['Current surface_pressure'],
        pressure=citi_weather['Current wind_speed_10m']
    )
    session.add(new_citi)
    await session.commit()
    return {'citi is add': True}


# Функция для получения списка городов
@app.get('/weather/get_all_cities')
async def get_all_cities() -> dict:
    all_cities: dict = {'all_cities': []}
    async with session_maker() as session:
        result = await session.execute(select(Cities))
        cities = result.scalars().all()
        for city in cities:
            city_name = city.citiName
            all_cities['all_cities'].append(city_name)
        return all_cities


# Функция для получения информации о погоде по названию города
@app.get('/weather/forecast')
async def get_weather_forecast(
        city: str,
        time: str,
        parameters: list[str] = Query(["temperature", "humidity", "wind_speed", "precipitation"])
):
    coordinates = await get_coordinates(city)
    if not coordinates:
        return {"error": "Город не найден"}

    latitude, longitude = coordinates

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"],
        "timezone": "auto"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if "hourly" not in data:
        return {"error": "Ошибка получения данных"}

    hourly_data = data["hourly"]
    forecast_times = hourly_data["time"]

    requested_time = datetime.strptime(time, "%H:%M").replace(second=0, microsecond=0).time()

    available_times = [
        datetime.strptime(t.split("T")[1][:5], "%H:%M").time() for t in forecast_times
    ]

    time_diffs = [abs((datetime.combine(datetime.today(), t) - datetime.combine(datetime.today(),
                                                                                requested_time)).total_seconds()) for t
                  in available_times]
    closest_index = np.argmin(time_diffs)

    forecast = {}
    if "temperature" in parameters:
        forecast["temperature"] = hourly_data["temperature_2m"][closest_index]
    if "humidity" in parameters:
        forecast["humidity"] = hourly_data["relative_humidity_2m"][closest_index]
    if "wind_speed" in parameters:
        forecast["wind_speed"] = hourly_data["wind_speed_10m"][closest_index]
    if "precipitation" in parameters:
        forecast["precipitation"] = hourly_data["precipitation"][closest_index]

    return {
        "city": city,
        "requested_time": time,
        "closest_time": available_times[closest_index].strftime("%H:%M"),
        "forecast": forecast
    }


if __name__ == "__main__":
    uvicorn.run('script:app', reload=True)
