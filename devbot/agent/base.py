import abc
import os
from typing import List, Callable, Dict, Tuple

import github
from git import Repo
from langchain.chat_models.base import BaseChatModel
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools import BaseTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.tools import tool
from langchain.tools.base import BaseTool

from devbot.agent.toolkit import GitToolkit


class DevAgent(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def _get_memory(self) -> List:
        pass

    @abc.abstractmethod
    def _get_tools(self) -> List[BaseTool]:
        pass

    @abc.abstractmethod
    def _get_prompt(self) -> ChatPromptTemplate:
        pass

    @abc.abstractmethod
    def _get_chat_model(self) -> BaseChatModel:
        pass

    def _get_inputs(self) -> Tuple[str, Dict[str, Callable]]:
        memory = self._get_memory()
        chat_history = memory[:-1]
        input = memory[-1]
        data = {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
            "chat_history": lambda x: x.get("chat_history") or chat_history,
        }
        return input, data

    def _run(self) -> str:
        llm = self._get_chat_model()
        tools = self._get_tools()
        tool_functions = [
            format_tool_to_openai_function(t) for t in self._get_tools()
        ]
        llm_with_tools = llm.bind(functions=tool_functions)

        input, inputs = self._get_inputs()

        use_prompt = self._get_prompt()
        agent = (
            inputs
            | use_prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        ).with_config(run_name=self.name)

        agent_executor = AgentExecutor(agent=agent, tools=tools)  # type: ignore
        resp = agent_executor.invoke({"input": input.content})  # type: ignore
        return resp["output"]

    def run(self) -> str:
        return self._run()

    # TODO: Add aiofiles method


class IssueAgent(DevAgent):
    def __init__(self, git_server: github.Github, repo_url: str, issue_number):
        self.git_server = git_server
        self.repo_name = self.get_repo_name_from_url(repo_url)
        self.issue_number = issue_number
        self.code_dir = self.prepare_env(repo_url)

    @staticmethod
    def get_repo_name_from_url(repo_url):
        host = "https://github.com/"
        return repo_url[len(host) :]

    def prepare_env(self, repo_url: str, commit_id: str = "master") -> str:
        local_dir = (
            f"./.agent_cache/{self.repo_name}@{commit_id}@{self.issue_number}"
        )
        if os.path.isdir(local_dir):
            repo = Repo(local_dir)
            repo.remotes.origin.pull()
        else:
            repo = Repo.clone_from(repo_url, local_dir)
        return local_dir

    @property
    def name(self):
        return "Issue"

    def _get_issue_chat_history(self):
        repo = self.git_server.get_repo(self.repo_name)
        ai_user = self.git_server.get_user().login
        issue = repo.get_issue(number=self.issue_number)
        chat_history = []
        if issue.user == ai_user:
            msg = AIMessage(content=issue.body)
        else:
            msg = HumanMessage(content=issue.body)
        chat_history.append(msg)
        for c in issue.get_comments():
            if c.user.login == ai_user:
                msg = AIMessage(content=c.body)
            else:
                msg = HumanMessage(content=c.body)
            chat_history.append(msg)
        return chat_history

    def _get_project_info(self):
        git_toolkit = GitToolkit(root_dir=self.code_dir)
        tools = git_toolkit.get_tools()
        tool = [t for t in tools if t.name == "list_directory"][0]
        files_list = tool.run({})
        return SystemMessage(content=f"file list: {files_list}")

    def _get_memory(self):
        chat_history = self._get_issue_chat_history()
        project_info = self._get_project_info()
        chat_history.insert(0, project_info)
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()
        git_toolkit = GitToolkit(root_dir=self.code_dir)
        tools.extend(git_toolkit.get_tools())
        return tools

    def _get_prompt(self):
        issue_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are very powerful coding assistant."
                    "Please answer the question based on the actual contents of repo."
                    "You are allowed to use tools to view "
                    "the repository and specific files",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return issue_prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k")
