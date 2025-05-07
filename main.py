import uvicorn
from fastapi import FastAPI
from routers.webhook import webhook_router
from config.config import Config

app = FastAPI()

app.include_router(webhook_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)
