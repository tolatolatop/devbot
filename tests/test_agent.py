#!/usr/bin/env python

"""Tests for `devbot` package."""

import os
import pytest

from dotenv import load_dotenv
import github

from devbot.agent.base import IssueAgent
from .data.agent import read_file, memory_tasks


@pytest.fixture
def git_server():
    load_dotenv()
    auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    g = github.Github(auth=auth)
    return g


@pytest.fixture
def issue_agent(git_server):
    agent = IssueAgent(
        git_server,
        read_file[0]["repo_url"],
        read_file[0]["issue_number"],
    )
    return agent


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("get_memory", "expected"), memory_tasks)
def test_tasks(issue_agent, get_memory, expected):
    agent = issue_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("stabled")
def test_get_memory(issue_agent):
    agent = issue_agent
    memory = agent._get_memory()
    assert "环境变量" in memory[0].content
