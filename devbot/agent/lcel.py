import re
from typing import Union

from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.output_parsers.react_single_input import (
    FINAL_ANSWER_ACTION,
    FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE,
)
from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.schema import AgentAction, AgentFinish, OutputParserException

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
)


class WriteReactParser(ReActSingleInputOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        includes_answer = FINAL_ANSWER_ACTION in text
        if includes_answer:
            regex = (
                r"Action\s*\d*\s*:[\s]*write_file[\s]*"
                r"Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*?)"
                r"Content\s*\d*\s*:(.*)Thought"
            )
            action_match = re.search(regex, text, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip()
                file_path = action_match.group(1).strip()
                content = action_match.group(2)
                tool_input = {"file_path": file_path, "text": content}
                finally_answer = text.split(FINAL_ANSWER_ACTION)[-1].strip()
                return AgentFinish(
                    {
                        "output": finally_answer,
                        "file_path": file_path,
                        "text": content,
                    },
                    text,
                )
            raise OutputParserException(
                f"{FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE}: {text}"
            )

        return super().parse(text)

    @property
    def _type(self) -> str:
        return "react-single-input"


class ReactAgentFactory:
    def write_agent(self, code_dir: str):
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

        prompt = prompt.partial(
            tools=render_text_description(tools),
            tool_names=", ".join([t.name for t in tools]),
        )

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
        return agent
        resp = agent.invoke(
            {"input": "add a sum fn to src/main.rs for add two number"}
        )
