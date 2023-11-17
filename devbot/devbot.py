import logging
import os

from fastapi import FastAPI, BackgroundTasks

from .repo.gitee import Gitee

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
    git_app = Gitee()
    git_app.auth(None, None)
    if event.sender.login != git_app.get_user().login:
        background_tasks.add_task(
            core.replay_issue,
            event.repository.full_name,
            event.repository.clone_url,
            "master",
            event.issue.number,
        )
    return {"message": "OK"}
