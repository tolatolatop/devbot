from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools.base import BaseTool
from langchain.tools.file_management.utils import BaseFileToolMixin
from langchain.tools.file_management.write import (
    WriteFileTool as BaseWriteFileTool,
)
from devbot.agent.agent_tool import PlanQueryAgent, WriteAgent
from devbot.agent import agent_tool


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


class PlanInput(BaseModel):
    """Input for WriteFileTool."""

    task: str = Field(..., description="task that require planning")


class InfoPlanTool(BaseFileToolMixin, BaseTool):
    """Tool that generate plans for tasks."""

    name: str = "create_collect_plan"
    args_schema: Type[BaseModel] = PlanInput
    description: str = "Tool that generate information collection plan."

    def _run(
        self,
        task: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            agent = PlanQueryAgent(self.root_dir, task)
            return agent.run()
        except Exception as e:
            return "Error: " + str(e)


class ToDoPlanInput(BaseModel):
    """Input for WriteFileTool."""

    task: str = Field(..., description="task that require planning")
    task_info: str = Field(..., description="Information related to the task")


class ToDoPlanTool(BaseFileToolMixin, BaseTool):
    """Tool that generate plans for tasks."""

    name: str = "create_coding_plan"
    args_schema: Type[BaseModel] = PlanInput
    description: str = "Tool that generate a coding plan."

    def _run(
        self,
        task: str,
        task_info: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            agent = agent_tool.PlanToDoAgent(self.root_dir, task, task_info)
            return agent.run()
        except Exception as e:
            return "Error: " + str(e)
