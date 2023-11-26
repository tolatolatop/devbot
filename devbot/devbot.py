import logging
import os

from fastapi import FastAPI, BackgroundTasks
from github import Github
from github import Auth
from pygitee.api import UserApi

from .repo import github
from .repo import gitee
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
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth)
    if event.sender.login != g.get_user().login:
        background_tasks.add_task(
            core.replay_issue,
            event.repository.full_name,
            event.repository.clone_url,
            "master",
            event.issue.number,
        )
    return {"message": "OK"}


@app.post("/webhook/gitee")
async def webhook_gitee(
    event: gitee.IssueEvent, background_tasks: BackgroundTasks
):
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth)
    if event.sender.login != g.get_user().login:
        background_tasks.add_task(
            core.replay_issue,
            event.repository.full_name,
            event.repository.clone_url,
            "master",
            event.issue.number,
        )
    return {"message": "OK"}
