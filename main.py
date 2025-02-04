import uvicorn
from fastapi import FastAPI, Depends
import openmeteo_requests
from sqlalchemy.ext.asyncio import create_async_engine, async_session, AsyncSession
from pydantic import BaseModel

from typing import Annotated

import httpx
import asyncio

from db.engine import create_db, engine,session_maker
from db.models.cities import Cities


import requests_cache
import pandas as pd
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
from sqlalchemy.future import select

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


# Ручка для создания бд
@app.post('/setup')
async def add_cities():
    await create_db()

# Ручка для получения данных о погоде по координатам в настоящий момент
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

# Ручка для добавления города в БД
@app.post('/weather/add_citi')
async def add_citi(citi_name: str, session: SessionDep):
    citi_coord = await get_coordinates(citi_name)
    citi_weather = await get_weather_now(citi_coord[0],citi_coord[1])

    new_citi = Cities(
        citiName = citi_name,
        temp=citi_weather['Current temperature_2m'],
        speed=citi_weather['Current surface_pressure'],
        pressure=citi_weather['Current wind_speed_10m']
    )
    session.add(new_citi)
    await session.commit()
    return {'citi is add': True}

@app.get('/weather/get_all_cities')
async def get_all_cities()->dict:
    all_cities: dict = {'all_cities':[]}
    async with session_maker() as session:
        result = await session.execute(select(Cities))
        cities = result.scalars().all()
        for city in cities:
            city_name = city.citiName
            all_cities['all_cities'].append(city_name)
        return all_cities


if __name__ == "__main__":
    uvicorn.run('main:app', reload=True)
