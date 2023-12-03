from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools.file_management.write import (
    WriteFileTool as BaseWriteFileTool,
)
from devbot.agent.agent_tool import WriteAgent


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
