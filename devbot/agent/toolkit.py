import subprocess as sp
from typing import List

from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.callbacks.manager import CallbackManagerForToolRun
import os
from typing import List, Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools.base import BaseTool
from langchain.tools.file_management.utils import BaseFileToolMixin
from langchain.tools.file_management.write import (
    WriteFileTool as BaseWriteFileTool,
)
from devbot.agent.agent_tool import WriteAgent


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
