#!/usr/bin/env python

"""Tests for `devbot` package."""

import imp
import pytest
from .data.repo import webhook_test_data

from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from langchain.tools.render import format_tool_to_openai_function
from langchain.schema.messages import HumanMessage, AIMessage

from devbot.agent.prompts import api_coding_prompt

from dotenv import load_dotenv


def test_agent():
    load_dotenv()

    llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
    chat_history = [HumanMessage(content=open("openapi.html", "r").read())]

    agent = (
        {
            "input": lambda x: x["input"],
            "chat_history": lambda x: x.get("chat_history") or chat_history,
        }
        | api_coding_prompt
        | llm
        | OpenAIFunctionsAgentOutputParser()
    ).with_config(run_name="Coding Agent")

    agent_executor = AgentExecutor(agent=agent, tools=[])

    r = agent_executor.invoke(
        {"input": "create a openapi.json from before document"}
    )
    print(r)
