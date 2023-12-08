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
from devbot.agent.bitbake import GitHubToolkit


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


def test_react(github_tools):
    prompt = """
Answer the following questions as best you can. You have access to the following tools:

{tools}
TIPS:
{tips}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
    prompt = ChatPromptTemplate.from_template(prompt)
    tools = github_tools

    llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
    llm = llm.bind(stop=["\nObservation"])
    react = (
        {
            "tips": lambda x: "",
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(
                x["intermediate_steps"]
            ),
            "tools": lambda x: render_text_description(tools),
            "tool_names": lambda x: ", ".join([t.name for t in tools]),
        }
        | prompt
        | llm
        | ReActSingleInputOutputParser()
    )
    agent = AgentExecutor(agent=react, tools=tools)  # type: ignore
    resp = agent.invoke({"input": "仓库里是否存在README文件"})
    assert "output" in resp
    assert "README" in resp["output"]
