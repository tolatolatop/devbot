import logging

from fastapi import FastAPI, BackgroundTasks

from devbot.repo import github

from devbot.controller import accept_event

app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/healthz")
async def healthz():
    return {"message": "OK"}
