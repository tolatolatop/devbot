import logging

from fastapi import FastAPI, BackgroundTasks

from devbot.repo import github
from devbot.agent import core

from devbot.controller import accept_event

app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/healthz")
async def healthz():
    return {"message": "OK"}


@app.post("/webhook/github")
async def webhook_github(
    event: github.IssueEvent, background_tasks: BackgroundTasks
):
    g = accept_event(event)
    if g:
        background_tasks.add_task(core.reslove_issue, event, g)
    return {"message": "OK"}
