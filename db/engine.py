import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.base import Base

engine = create_async_engine("sqlite+aiosqlite:///mydb.db", echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Функция создания таблиц
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция удаления таблиц
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)