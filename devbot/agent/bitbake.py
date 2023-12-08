import os

from typing import Optional, List, Type, Any
from operator import itemgetter

from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.utilities.github import GitHubAPIWrapper
from github import Auth, Github, ContentFile
from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools.file_management.list_dir import DirectoryListingInput
from langchain.tools.file_management.read import ReadFileInput
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.globals import set_verbose
from langchain.schema.runnable import RunnableLambda

from langchain.tools.render import render_text_description
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import ChatPromptTemplate
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
)
from langchain.schema.output_parser import StrOutputParser


from github import Github
from github.Repository import Repository


class BaseGithubToolMixin(BaseModel):
    github: Any
    repo: str
    revision: str = ""

    def _get_repo(self) -> Repository:
        return self.github.get_repo(self.repo)

    def _get_contents(self, path: str):
        repo = self._get_repo()
        return repo.get_contents(path, ref=self.revision)


class GitHubToolkit(BaseToolkit):
    github: Any
    repo: str
    revision: str = "master"

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        tools: List[BaseTool] = []
        for tool_cls in [ListTreeTool, ReadFileTool]:
            tool_cls: BaseGithubToolMixin
            tool = tool_cls(
                github=self.github, repo=self.repo, revision=self.revision
            )  # type: ignore
            tools.append(tool)
        return tools


class ListTreeTool(BaseGithubToolMixin, BaseTool):
    """Tool that lists files and directories in a specified folder."""

    name: str = "list_directory"
    args_schema: Type[BaseModel] = DirectoryListingInput
    description: str = "List files and directories in a specified folder"

    def _run(
        self,
        dir_path: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            dir_path = "" if " " in dir_path else dir_path
            contents = self._get_contents(dir_path)
            if not isinstance(contents, List):
                raise ValueError(f"{dir_path} not a dir")
            # Initialize an empty list to store the file names
            file_names = []

            # Iterate over the contents and add file names to the list
            for content in contents:
                assert isinstance(content, ContentFile.ContentFile)
                if content.type == "dir":
                    file_names.append(f"{content.name}/")
                else:
                    file_names.append(content.name)
            return "\n".join(file_names)
        except Exception as e:
            return f"Error: no found {dir_path}"


class ReadFileTool(BaseGithubToolMixin, BaseTool):
    """Tool that reads a file."""

    name: str = "read_file"
    args_schema: Type[BaseModel] = ReadFileInput
    description: str = "Read file from disk"

    def _run(
        self,
        file_path: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            file = self._get_contents(file_path)
            if not isinstance(file, ContentFile.ContentFile):
                raise ValueError(f"{file_path} not a file")
            return file.decoded_content.decode("utf-8")
        except Exception as e:
            return f"Error: no found {file_path}"


class BitbakeAgentFactory:
    def create_github_agent(
        self, git_server: Github, repo: str, revision: str
    ):
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
        tools = GitHubToolkit(
            github=git_server, repo=repo, revision=revision
        ).get_tools()

        llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
        llm = llm.bind(stop=["\nObservation"])
        llm_chain = (
            {
                "tips": lambda x: x.get("tips") or "",
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
        agent = AgentExecutor(agent=llm_chain, tools=tools, handle_parsing_errors=True)  # type: ignore
        return agent

    def create_repice_agent(
        self, git_server: Github, repo: str, revision: str
    ):
        prompt = """
Answer the following questions as best you can.

ORIGIN FILE CONTENT:
{content}

COMPILE GUIDE:
{compile_guide}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Final Answer: the final answer to the original input question

Begin!

Question: Improve the content of ORIGIN FILE CONTENT according to COMPILE GUIDE. The content comes from the recipe file written in bitbake language.
Thought: {agent_scratchpad}
    """
        prompt = ChatPromptTemplate.from_template(prompt)

        llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
        llm = llm.bind(stop=["\nObservation"])
        compile_guide_agent = self.create_github_agent(
            git_server, repo, revision
        )
        sub_q = {
            "input": lambda x: QUEST_OF_GENERATE_COMPILE_GUIDE,
            "tips": lambda x: TIPS_GENERATE_COMPILE_GUIDE,
        }
        llm_chain = (
            {
                "compile_guide": sub_q
                | compile_guide_agent
                | RunnableLambda(lambda x: x["output"]),
                "content": itemgetter("input"),
                "agent_scratchpad": lambda x: format_log_to_str(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm
            | ReActSingleInputOutputParser()
        )
        agent = AgentExecutor(agent=llm_chain, tools=[], handle_parsing_errors=True)  # type: ignore
        return agent


TIPS_GENERATE_COMPILE_GUIDE = """The following files or directories may contain build instructions:
INSTALL
README
build script
git action
Makefile
configure
./src
"""

QUEST_OF_GENERATE_COMPILE_GUIDE = (
    "Generate a guide of 300 words or less telling users how to compile and install."
    "If you can't find any build instructions, you can make up your own mind based on your project structure."
)
