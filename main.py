import uvicorn
from fastapi import FastAPI

from sqlalchemy.ext.asyncio import create_async_engine, async_session

engine = create_async_engine('sqlite+aiosqlite:///weather.db')
app = FastAPI()


@app.get('/')
def root():
    return 'hi'



if __name__ == "__main__":
    uvicorn.run('main:app', reload=True)