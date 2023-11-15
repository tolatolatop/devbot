import logging

from fastapi import FastAPI, BackgroundTasks

from .repo import github
from .agent import core

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
    background_tasks.add_task(
        core.replay_issue,
        event.repository.full_name,
        event.clone_url,
        "master",
        event.issue.number,
    )
    return {"message": "OK"}
