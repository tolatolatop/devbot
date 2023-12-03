#!/usr/bin/env python

"""Tests for `devbot` package."""

import os
import pytest
from unittest import mock

from dotenv import load_dotenv
import github
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage

from devbot.agent.base import IssueAgent
from .data.repo import read_file


@pytest.fixture
def git_server():
    load_dotenv()
    auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    g = github.Github(auth=auth)
    return g


@pytest.fixture
def read_file_memory():
    memory = [
        SystemMessage(
            content="filelist:\nDockerfile\n.env.template\nREADME.rst\n---\n"
        ),
        HumanMessage(content="解释项目中所有需要配置的环境变量"),
    ]
    return mock.Mock(return_value=memory)


def test_agent(git_server, read_file_memory):
    agent = IssueAgent(
        git_server,
        read_file[0]["repo_url"],
        read_file[0]["issue_number"],
    )
    agent._get_memory = read_file_memory
    resp = agent.run()
    assert "LANGCHAIN_TRACING_V2" in resp
