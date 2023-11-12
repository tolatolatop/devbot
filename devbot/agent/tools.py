from genericpath import isfile
import uuid
import os
import subprocess as sp

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


@tool
def list_files(callbacks: Callbacks = None):
    """list all files in repo"""
    files = []
    p = sp.Popen(
        ["git", "ls-tree", "--full-tree", "--name-only", "-r", "HEAD"],
        cwd=".",
        stdout=sp.PIPE,
        stderr=sp.PIPE,
    )
    stdout, _ = p.communicate()
    text = stdout.decode()
    return text


@tool
def read_files(file_path: str, callbacks: Callbacks = None):
    """read specify file in repo"""
    if os.path.isfile(file_path) and file_path != ".env":
        with open(file_path, "r") as f:
            return f.read()
    return f"some wrong happend when read {file_path}. Maybe {file_path} is not exists or not a file. Please use list_files to check"
