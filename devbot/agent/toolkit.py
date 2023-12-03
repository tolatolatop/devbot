import subprocess as sp
from langchain.callbacks.manager import CallbackManagerForToolRun
import os
from typing import Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools.base import BaseTool
from langchain.tools.file_management.utils import BaseFileToolMixin


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