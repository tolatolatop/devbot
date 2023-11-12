import uuid
import os
import subprocess as sp
from git import Repo

import requests
from langchain.callbacks.manager import Callbacks
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.tools import tool


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

    return [list_files, read_files]


def prepare_env(repo_url: str, repo_name: str, commit_id: str = "master"):
    local_dir = f"./.agent_cache/{repo_name}@{commit_id}"
    if os.path.isdir(local_dir):
        repo = Repo(local_dir)
        repo.active_branch.checkout(True)
    else:
        repo = Repo.clone_from(repo_url, local_dir)
    return local_dir
