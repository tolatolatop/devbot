import uuid
import os
import subprocess as sp

from git import Repo
from github import Github
from github import Auth
import requests
from langchain.callbacks.manager import Callbacks
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.tools import tool
from langchain.schema.messages import HumanMessage, AIMessage


@tool
def summarize_tool(url: str, callbacks: Callbacks = None):
    """Summarize a website."""
    text = requests.get(url).text
    summary_chain = (
        ChatPromptTemplate.from_template(
            "Summarize the following text:\n<TEXT {uid}>\n"
            "{text}"
            "\n</TEXT {uid}>"
        ).partial(uid=lambda: uuid.uuid4())
        | ChatOpenAI(model="gpt-3.5-turbo-16k")
        | StrOutputParser()
    ).with_config(run_name="Summarize Text")
    return summary_chain.invoke(
        {"text": text},
        {"callbacks": callbacks},
    )


def create_filesystem_tools(root_path):
    @tool
    def list_files(callbacks: Callbacks = None):
        """list all files in repo"""
        p = sp.Popen(
            ["git", "ls-tree", "--full-tree", "--name-only", "-r", "HEAD"],
            cwd=root_path,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        stdout, _ = p.communicate()
        text = stdout.decode()
        return text

    @tool
    def read_files(file_path: str, callbacks: Callbacks = None):
        """read specify file in repo"""
        r_file_path = os.path.join(root_path, file_path)
        if os.path.isfile(r_file_path):
            with open(r_file_path, "r") as f:
                return f.read()
        err_msg = (
            f"some wrong happend when read {file_path}. Maybe {file_path}"
            " is not exists or not a file."
            "Please use list_files to check"
        )
        return err_msg

    @tool
    def run_make_cmd(target: str, Callbacks=None):
        """run make command like: make ${target}"""
        cmd = f"make {target}"
        p = sp.Popen(
            cmd,
            cwd=root_path,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=True,
        )
        stdout, stderr = p.communicate()
        text = (
            f"# {cmd}\n"
            f"stdout:\n{stdout.decode()}"
            "\n----\n"
            f"stderr:\n{stderr.decode()}"
        )
        return text

    return [list_files, read_files, run_make_cmd]


def comment_issue_by_github(g: Github, repo_name, issue_number, comment):
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(number=issue_number)
    res = issue.create_comment(comment)
    return res


def create_github_tools(g: Github, repo_url, repo_name, issue_number):
    @tool
    def comment_issue(comment, Callbacks=None):
        """comment issue"""
        res = comment_issue_by_github(g, repo_name, issue_number, comment)
        return res

    return [comment_issue]


def prepare_env(repo_url: str, repo_name: str, commit_id: str = "master"):
    local_dir = f"./.agent_cache/{repo_name}@{commit_id}"
    if os.path.isdir(local_dir):
        repo = Repo(local_dir)
        repo.remotes.origin.pull()
    else:
        repo = Repo.clone_from(repo_url, local_dir)
    return local_dir


def create_issue_chat_history(g: Github, repo_name: str, issue_number: int):
    repo = g.get_repo(repo_name)
    ai_user = g.get_user().login
    issue = repo.get_issue(number=issue_number)
    chat_history = []
    if issue.user == ai_user:
        msg = AIMessage(content=issue.body)
    else:
        msg = HumanMessage(content=issue.body)
    chat_history.append(msg)
    for c in issue.get_comments():
        if c.user.login == ai_user:
            msg = AIMessage(content=c.body)
        else:
            msg = HumanMessage(content=c.body)
        chat_history.append(msg)
    return chat_history


if __name__ == "__main__":
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth)
    repo_name = "tolatolatop/devbot"
    issue_number = 5
    res = create_issue_chat_history(g, repo_name, issue_number)
    print(res)
