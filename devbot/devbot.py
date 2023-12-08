import logging
import os

from fastapi import FastAPI, BackgroundTasks

from devbot.repo import github

from devbot.agent.bitbake import BitbakeAgentFactory

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
            "input": "获取构建方法并用200字内总结",
            "tips": """以下文件或目录中可能包含构建指导:
INSTALL
README
./src
如果找不到构建指导，你可以根据项目目录结构自行生成
""",
        }
    )
    return resp["output"]
