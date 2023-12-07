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
from devbot.agent.lcel import WriteReactParser


@pytest.mark.skip("pass")
def test_dict_chain():
    prompt1 = ChatPromptTemplate.from_template(
        "what is the city {person} is from?"
    )
    prompt2 = ChatPromptTemplate.from_template(
        "what country is the city {city} in? respond in {language}"
    )

    model = ChatOpenAI()

    chain1 = prompt1 | model | StrOutputParser()

    chain2 = (
        {
            "city": chain1,
            "language": itemgetter("language"),
        }  # 允许chain结果作为参数 公用输入
        | prompt2
        | model
        | StrOutputParser()
    ).with_config(name="abc", verbose=True)

    resp = chain2.invoke({"person": "obama", "language": "spanish"})
    assert "Honolulu" in resp


@pytest.mark.skip("pass")
def test_memory_history():
    REDIS_URL = os.environ.get("REDIS_URL")

    chain = RunnableParallel({"output_message": ChatOpenAI()})
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: RedisChatMessageHistory(session_id, url=REDIS_URL),
        output_messages_key="output_message",
    )

    resp = chain_with_history.invoke(
        [
            HumanMessage(
                content="What did Simone de Beauvoir believe about free will"
            )
        ],
        config={"configurable": {"session_id": "baz"}},
    )

    resp2 = chain_with_history.invoke(
        [HumanMessage(content="How did this compare to Sartre")],
        config={"configurable": {"session_id": "baz"}},
    )

    assert "cosine" in resp2


@pytest.mark.skip("pass")
def test_chain_branch():
    planner = (
        ChatPromptTemplate.from_template("Generate an argument about: {input}")
        | ChatOpenAI()
        | StrOutputParser()
        | {"base_response": RunnablePassthrough()}
    )

    arguments_for = (
        ChatPromptTemplate.from_template(
            "List the pros or positive aspects of {base_response}"
        )
        | ChatOpenAI()
        | StrOutputParser()
    )
    arguments_against = (
        ChatPromptTemplate.from_template(
            "List the cons or negative aspects of {base_response}"
        )
        | ChatOpenAI()
        | StrOutputParser()
    )

    final_responder = (
        ChatPromptTemplate.from_messages(
            [
                ("ai", "{original_response}"),
                ("human", "Pros:\n{results_1}\n\nCons:\n{results_2}"),
                ("system", "Generate a final response given the critique"),
            ]
        )
        | ChatOpenAI()
        | StrOutputParser()
    )

    chain = (
        planner
        | {
            "results_1": arguments_for,
            "results_2": arguments_against,
            "original_response": itemgetter("base_response"),
        }
        | final_responder
    )
    resp = chain.invoke({"input": "scrum"})
    assert "Scrum" in resp


@pytest.fixture
def git_server():
    import github

    auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    g = github.Github(auth=auth)
    return g


@pytest.fixture
def issue_agent(git_server):
    from devbot.agent.coding import IssueAgent

    agent = IssueAgent(
        git_server,
        data_lcel.read_file[0]["repo_url"],
        data_lcel.read_file[0]["issue_number"],
    )
    return agent


@pytest.fixture
def code_dir(issue_agent):
    code_dir = issue_agent.prepare_env(
        data_lcel.read_file[0]["repo_url"],
    )
    return code_dir


@pytest.mark.skip("yes")
def test_react(code_dir):
    prompt = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

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
    tools = FileManagementToolkit(
        root_dir=code_dir, selected_tools=["read_file"]
    ).get_tools()

    llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
    llm = llm.bind(stop=["\nObservation"])
    react = (
        {
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
    resp = agent.invoke({"input": "summary src/main.rs"})
    assert "finall_answer" in resp
    assert "Gitee API Client" in resp["finall_answer"]


def test_write(code_dir):
    prompt = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Action: write_file
Action Input:  file path you want to modify
Content: Modified file content
Final Answer: Summary of changes

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
    prompt = ChatPromptTemplate.from_template(prompt)
    tools = FileManagementToolkit(
        root_dir=code_dir, selected_tools=["read_file"]
    ).get_tools()

    llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
    llm = llm.bind(stop=["\nObservation"])
    react = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(
                x["intermediate_steps"]
            ),
            "tools": lambda x: render_text_description(tools),
            "tool_names": lambda x: ", ".join([t.name for t in tools]),
        }
        | prompt
        | llm
        | WriteReactParser()
    )
    agent = AgentExecutor(agent=react, tools=tools)  # type: ignore
    resp = agent.invoke(
        {"input": "add a sum fn to src/main.rs for add two number"}
    )
    assert isinstance(resp, dict)
    assert "Thought" not in resp["text"]
    assert "main.rs" in resp["file_path"]
    assert "sum" in resp["text"]


def test_write_react_parser():
    text = """
The content of the file src/main.rs does not currently have a sum function. I need to add a sum function that takes two numbers as input and returns their sum.

Action: write_file
Action Input: src/main.rs
Content: use clap::{App, Arg};

fn main() {
    // Create a new instance of the command-line application
    let app = App::new(env!("CARGO_PKG_NAME"))
        .version(env!("CARGO_PKG_VERSION"))
        .author(env!("CARGO_PKG_AUTHORS"))
        .about(env!("CARGO_PKG_DESCRIPTION"))
        // Define the command-line arguments
        .arg(
            Arg::with_name("input")
                .help("Input file")
                .index(1)
                .required(true),
        )
        .arg(
            Arg::with_name("output")
                .help("Output file")
                .index(2)
                .required(true),
        );

    // Parse the command-line arguments
    let matches = app.get_matches();

    // Access the values of the arguments
    let input_file = matches.value_of("input").unwrap();
    let output_file = matches.value_of("output").unwrap();

    // Your application logic goes here

    println!("Input file: {}", input_file);
    println!("Output file: {}", output_file);
}

fn sum(a: i32, b: i32) -> i32 {
    a + b
}

Thought: I have modified the file src/main.rs to add the sum function for adding two numbers.

Final Answer: I have added a sum function to src/main.rs for adding two numbers.
"""
    resp = WriteReactParser().parse(text)
    assert isinstance(resp, AgentFinish)
    assert "output" in resp.return_values
    assert "file_path" in resp.return_values
    assert "text" in resp.return_values
    assert "Thought" not in resp.return_values["text"]


@pytest.mark.skip("yes")
def test_use_python():
    template = """Write some python code to solve the user's problem. 

    Return only python code in Markdown format, e.g.:

    ```python
    ....
    ```"""
    prompt = ChatPromptTemplate.from_messages(
        [("system", template), ("human", "{input}")]
    )

    model = ChatOpenAI()

    def _sanitize_output(text: str):
        _, after = text.split("```python")

        return after.split("```")[0]

    chain = (
        prompt
        | model
        | StrOutputParser()
        | _sanitize_output
        | {"output": RunnablePassthrough()}
    )
    resp = chain.invoke({"input": "whats 2 plus 2"})
    assert "output" in resp
    assert "print" in resp["output"]
