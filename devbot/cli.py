"""Console script for devbot."""
import argparse
import sys
import re
from typing import Union

from langchain.schema import AgentAction, AgentFinish
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, StrOutputParser
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from langchain.callbacks import HumanApprovalCallbackHandler

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from dotenv import load_dotenv

load_dotenv()


def _should_check(serialized_obj: dict) -> bool:
    return True


def _approve(_input: str) -> bool:
    msg = (
        "Do you approve of the following input? "
        "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
    )
    msg += "\n\n" + _input + "\n"
    resp = input(msg)
    return resp.lower() in ("yes", "y")


def run(root_dir):
    role = """"""
    example = """"""
    format = """"""
    eval = ""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", role),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ],
    )
    callbacks = [
        HumanApprovalCallbackHandler(
            should_check=_should_check, approve=_approve
        )
    ]
    memory = ConversationBufferMemory(
        return_messages=True, output_key="output", input_key="input"
    )

    llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
    tools = load_tools(
        ["wikipedia", "llm-math"],
        llm=llm,
        callbacks=callbacks,  # type: ignore
    )
    tool_functions = [format_tool_to_openai_function(t) for t in tools]
    llm = llm.bind(functions=tool_functions)

    inputs = {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_functions(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: memory.load_memory_variables({}["history"]),
    }

    chain = inputs | prompt | llm | OpenAIFunctionsAgentOutputParser()
    agent = AgentExecutor(
        agent=chain,  # type: ignore
        tools=tools,
        handle_parsing_errors=True,
        callbacks=callbacks,  # type: ignore
    )
    FIRST_QUESTION = "Introduce yourself and what you can do in 100 words."
    resp = agent.invoke({"input": FIRST_QUESTION})
    while True:
        answer = resp["output"]
        print(f"AI   :{answer}")
        quest = input(f"HUMAN:")
        if quest == "exit":
            return True
        resp = agent.invoke({"input": quest})
        memory.save_context(
            {"input": resp["input"]}, {"output": resp["output"]}
        )


def main():
    """Console script for devbot."""
    parser = argparse.ArgumentParser()
    parser.add_argument("_")
    args = parser.parse_args()

    print("Arguments: " + str(args))
    run(args._)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
