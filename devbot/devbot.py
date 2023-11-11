import logging

from fastapi import FastAPI

from .repo import github

app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/healthz")
async def healthz():
    return {"message": "OK"}


@app.post("/webhook/github")
async def webhook_github(event: github.AllEvent):
    logger.info(event)
    return {"message": "OK"}
