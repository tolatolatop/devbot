#!/usr/bin/env python

"""Tests for `devbot` package."""

import os
import pytest

from dotenv import load_dotenv
import github

from devbot.agent.coding import CodingAgent, PlanAgent
from devbot.agent.coding import IssueAgent
from devbot.agent.toolkit import WriteFileTool
from devbot.agent import agent_tool
from devbot.agent.checklist import MetaChecklistAgent, FormattedChecklistAgent
from devbot.agent.checklist import GenChecklistAgent, DoChecklistAgent
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


@pytest.fixture
def plan_agent(git_server):
    agent = PlanAgent(
        git_server,
        read_file[0]["repo_url"],
        read_file[0]["issue_number"],
    )
    return agent


@pytest.fixture
def meta_checklist_agent(git_server):
    agent = MetaChecklistAgent()
    return agent


@pytest.fixture
def code_dir(issue_agent):
    code_dir = issue_agent.prepare_env(
        read_file[0]["repo_url"],
    )
    return code_dir


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("get_memory", "expected"), memory_tasks)
def test_tasks(issue_agent, get_memory, expected):
    agent = issue_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("get_memory", "expected"), tasks.coding_tasks)
def test_coding_tasks(coding_agent, get_memory, expected):
    agent = coding_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("get_memory", "expected"), tasks.coding_plan_tasks)
def test_coding_plan_tasks(plan_agent, get_memory, expected):
    agent = plan_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(
    ("get_memory", "expected"), tasks.checklist_agent_tasks
)
def test_checklist_agent(meta_checklist_agent, get_memory, expected):
    agent = meta_checklist_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert resp.startswith("Checklist:")
    assert expected == resp.count("- [ ]")


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("plan", "task_number"), tasks.task_plan)
def test_formatted_checklist_agent(plan, task_number):
    agent = FormattedChecklistAgent(plan)
    resp = agent.run()
    assert resp.startswith("Checklist:")
    assert task_number == resp.count("- [ ]")


@pytest.mark.skip("no test")
@pytest.mark.parametrize(
    ("get_memory", "expected"), tasks.meta_checklist_agent_tasks
)
def test_meta_checklist_agent(meta_checklist_agent, get_memory, expected):
    agent = meta_checklist_agent
    agent._get_memory = get_memory
    resp = agent.run()
    assert resp.startswith("Checklist:")
    assert expected == resp.count("- [ ]")


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("file_path", "text", "task"), write_tasks)
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


@pytest.mark.parametrize(("task", "checklist"), tasks.do_checklist_agent_tasks)
def test_do_checklist_tasks(code_dir, task, checklist):
    gc_agent = DoChecklistAgent(
        code_dir=code_dir, task=task, checklist=checklist
    )
    resp = gc_agent.run()
    assert "main" in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("task",), tasks.plan_tasks)
def test_plan_tasks(code_dir, task):
    gc_agent = GenChecklistAgent(code_dir=code_dir, task=task)
    resp = gc_agent.run()
    assert "- [ ] READ" in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("task", "plan", "expected"), tasks.do_plan_tasks)
def test_do_plan_tasks(code_dir, task, plan, expected):
    agent = agent_tool.DoPlanAgent(code_dir, task, plan)
    resp = agent.run()
    assert expected in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("task", "task_info"), tasks.plan_to_do_tasks)
def test_plan_to_do_tasks(code_dir, task, task_info):
    agent = agent_tool.PlanToDoAgent(code_dir, task, task_info)
    resp = agent.run()
    assert "- [ ] MODIFY" in resp


@pytest.mark.skip("no test")
@pytest.mark.parametrize(("task", "plan", "task_info"), tasks.to_do_tasks)
def test_to_do_tasks(code_dir, task, plan, task_info):
    agent = agent_tool.ToDoAgent(code_dir, task, plan, task_info)
    resp = agent.run()
    assert "devbot/devbot.py" in resp
