import subprocess as sp
from typing import List, Callable, Dict, Tuple

from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.callbacks.manager import CallbackManagerForToolRun
import os
from typing import List, Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools.base import BaseTool
from langchain.tools.file_management.utils import BaseFileToolMixin
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.tools.file_management.write import (
    WriteFileTool as BaseWriteFileTool,
)
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from devbot.agent.base import DevAgent


class GitTreeListingInput(BaseModel):
    """Input for ListDirectoryTool."""


class ListTreeTool(BaseFileToolMixin, BaseTool):
    """Tool that lists all files in repo."""

    name: str = "list_directory"
    args_schema: Type[BaseModel] = GitTreeListingInput
    description: str = "Tool that lists all files in repo."

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            return self.__list_files()
        except Exception as e:
            return "Error: " + str(e)

    def __list_files(self):
        """list all files in repo"""
        cmd = ["git", "ls-tree", "--full-tree", "--name-only", "-r", "HEAD"]
        p = sp.Popen(
            cmd,
            cwd=self.root_dir,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=False,
        )
        stdout, stderr = p.communicate()
        text = (
            f"# {cmd}\n"
            f"stdout:\n{stdout.decode()}"
            "\n----\n"
            f"stderr:\n{stderr.decode()}"
            "\n----\n"
        )
        return text


class GitToolkit(BaseToolkit):
    root_dir: Optional[str] = None

    def get_tools(self) -> List[BaseTool]:
        return [ListTreeTool(root_dir=self.root_dir)]


class WriteFileInput(BaseModel):
    """Input for WriteFileTool."""

    file_path: str = Field(..., description="name of file")
    text: str = Field(..., description="text to write to file")
    task: str = Field(..., description="original description of the task")


class WriteAgent(DevAgent):
    def __init__(self, code_dir, file_path, text: str, task: str) -> None:
        super().__init__()
        self.code_dir = code_dir
        self.file_path = file_path
        self.text = text
        self.task = task

    @property
    def name(self):
        return "Write"

    def _get_memory(self):
        tool = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()[0]
        origin_content = tool.run({"file_path": self.file_path})
        chat_history = [
            SystemMessage(
                content=f"content of original file:\n{origin_content}"
            ),
            HumanMessage(content=f"Reference content:\n{self.text}"),
            AIMessage(content=f"I have memorized the above reference"),
            HumanMessage(
                content=f"1. {self.task}\n2. write to {self.file_path}"
            ),
        ]
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["write_file"],
        ).get_tools()
        return tools

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

    def _get_prompt(self):
        issue_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are very powerful coding assistant."
                    "Modify the content of the original file to comply with user requirements.",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return issue_prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class WriteFileTool(BaseWriteFileTool):
    """Tool that write file"""

    args_schema: Type[BaseModel] = WriteFileInput

    def _run(
        self,
        file_path: str,
        text: str,
        task: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            agent = WriteAgent(self.root_dir, file_path, text, task)
            return agent.run()
        except Exception as e:
            return "Error: " + str(e)
