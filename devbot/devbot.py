import logging
import os

from fastapi import FastAPI, BackgroundTasks

from devbot.repo import github
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough

from devbot.agent.bitbake import (
    BitbakeAgentFactory,
    TIPS_GENERATE_COMPILE_GUIDE,
    QUEST_OF_GENERATE_COMPILE_GUIDE,
)

app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/healthz")
async def healthz():
    return {"message": "OK"}


def get_git_server():
    import github

    auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    g = github.Github(auth=auth)
    return g


@app.get("/compile_guide")
def compile_guide(repo_name: str, revision: str = "master"):
    git_server = get_git_server()
    agent = BitbakeAgentFactory().create_github_agent(
        git_server, repo_name, revision
    )
    resp = agent.invoke(
        {
            "input": QUEST_OF_GENERATE_COMPILE_GUIDE,
            "tips": TIPS_GENERATE_COMPILE_GUIDE,
        }
    )
    return resp["output"]


@app.get("/imporve_recipe")
def imporve_recipe(question: str, repo_name: str, revision: str = "master"):
    git_server = get_git_server()
    agent = BitbakeAgentFactory().create_repice_agent(
        git_server, repo_name, revision
    )
    resp = agent.invoke(
        {
            "input": question,
        }
    )
    return resp["output"]
