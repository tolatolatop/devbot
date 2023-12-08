import os

from typing import Optional, List, Type, Any

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
            return "Error: " + str(e)


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
            return "Error: " + str(e)
