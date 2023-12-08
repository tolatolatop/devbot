from operator import itemgetter
import dotenv
import pytest
import os
import redis

from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.globals import set_verbose

from typing import Optional, Union

from langchain.tools.render import render_text_description
from langchain.chat_models import ChatAnthropic
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, StrOutputParser
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.schema.runnable import RunnableParallel
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.schema import AgentAction, AgentFinish, OutputParserException

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
)
from langchain.schema.output_parser import StrOutputParser

from .data import lcel as data_lcel
from devbot.agent.bitbake import (
    GitHubToolkit,
    BitbakeAgentFactory,
    TIPS_GENERATE_COMPILE_GUIDE,
)


@pytest.mark.skip("stable")
def test_github_toolkit(git_server):
    toolkit = GitHubToolkit(github=git_server, repo="mirror/busybox")
    tools = toolkit.get_tools()
    list_dir = tools[0]
    resp = list_dir.run({"dir_path": "."})
    assert "INSTALLXXX" in resp


@pytest.fixture
def github_tools(git_server):
    toolkit = GitHubToolkit(github=git_server, repo="mirror/busybox")
    tools = toolkit.get_tools()
    return tools


def test_compile_guide(git_server):
    repo_name = "niwasawa/c-hello-world"
    revision = "master"
    agent = BitbakeAgentFactory().create_github_agent(
        git_server, repo_name, revision
    )
    resp = agent.invoke(
        {
            "input": "获取构建方法并用200字内总结",
            "tips": TIPS_GENERATE_COMPILE_GUIDE,
        }
    )
    assert "output" in resp
    assert "README" in resp["output"]
