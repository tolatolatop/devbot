import re
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


class DoInfoPlanInput(BaseModel):
    """Input for WriteFileTool."""

    task: str = Field(..., description="task that require planning")
    plan: str = Field(
        ...,
        description="checklist waiting to be completed. "
        "Example:- [ ] READ devbot/devbot.py  # Check if there are any existing API endpoints and understand the code structure",
    )


class DoInfoPlanTool(BaseFileToolMixin, BaseTool):
    """Tool that generate plans for tasks."""

    name: str = "collect_helpful_information"
    args_schema: Type[BaseModel] = DoInfoPlanInput
    description: str = "Tools for completing information collection checklists"

    def _run(
        self,
        task: str,
        plan: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        infos = []
        try:
            for s_plan in self._iter_plan(plan):
                agent = agent_tool.DoPlanAgent(self.root_dir, task, s_plan)
                resp = agent.run()
                if "No helpful information" not in resp:
                    infos.append(resp)
            return "\n".join(infos)
        except Exception as e:
            return "Error: " + str(e)

    def _iter_plan(self, plan):
        all_plan = re.findall(r"\[ \].*", plan)
        if len(all_plan) == 0:
            raise ValueError("Please check the plan parameter format")
        for task in all_plan:
            yield task
