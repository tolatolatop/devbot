#!/usr/bin/env python

"""Tests for `devbot` package."""

import os
import pytest

from dotenv import load_dotenv
import github

from devbot.agent.coding import CodingAgent
from devbot.agent.coding import IssueAgent
from devbot.agent.toolkit import WriteFileTool, PlanTool
from .data.agent import read_file, memory_tasks, coding_tasks, write_tasks
from .data import agent as tasks


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


@pytest.fixture
def coding_agent(git_server):
    agent = CodingAgent(
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


@pytest.mark.xfail(run=False, reason="has bug")
@pytest.mark.parametrize(("get_memory", "expected"), coding_tasks)
def test_coding_tasks(coding_agent, get_memory, expected):
    agent = coding_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(
    ("code_dir", "file_path", "text", "task"), write_tasks
)
def test_write_tasks(code_dir, file_path, text, task):
    tool = WriteFileTool(root_dir=code_dir)
    resp = tool.run(
        {
            "file_path": file_path,
            "text": text,
            "task": task,
        }
    )
    assert "README.rst" in resp


@pytest.mark.parametrize(("code_dir", "task"), tasks.plan_tasks)
def test_plan_tasks(code_dir, task):
    tool = PlanTool(root_dir=code_dir)
    resp = tool.run(
        {
            "task": task,
        }
    )
    assert "- [ ] READ" in resp
