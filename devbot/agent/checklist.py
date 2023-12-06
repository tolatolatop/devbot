import re
from typing import Optional, Type

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools.base import BaseTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.tools.file_management.utils import BaseFileToolMixin


from devbot.agent.tools import GitToolkit
from devbot.agent.base import SimpleAgent, DevAgent


class ProjectAgent(SimpleAgent):
    def __init__(self, code_dir, task: str) -> None:
        super().__init__()
        self.code_dir = code_dir
        self.task = task

    def _get_project_info(self):
        git_toolkit = GitToolkit(root_dir=self.code_dir)
        tools = git_toolkit.get_tools()
        tool = [t for t in tools if t.name == "list_directory"][0]
        files_list = tool.run({})
        return SystemMessage(content=f"file list in project:\n {files_list}")

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class GenChecklistAgent(ProjectAgent):
    @property
    def name(self):
        return "GenProjTask"

    def _get_memory(self):
        chat_history = [
            self._get_project_info(),
            HumanMessage(content=f"{self.task}"),
        ]
        return chat_history

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are very powerful coding assistant.
Develop a plan for collecting information based on the user's tasks.
You only have read access, do not create or modify anything during the plan.
The generated plan must be less than 5 steps and can only use the read command and specify the operation object.
Example:
1. Modify the README.rst file to include project environment variable descriptions.
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "Task:\n{input}"),
            ]
        )
        return prompt

    def run(self) -> str:
        plan = super().run()
        formatted_agent = FormattedQueryChecklistAgent(plan)
        plan = formatted_agent.run()
        return plan


class DoChecklistAgent(DevAgent, ProjectAgent):
    def __init__(self, code_dir, task: str, checklist: str) -> None:
        super().__init__(code_dir=code_dir, task=task)
        self.checklist = checklist

    @property
    def name(self):
        return "DoChecklist"

    def _get_memory(self):
        chat_history = [
            HumanMessage(
                content=f"Original Task: {self.task}\n{self.checklist}"
            ),
        ]
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file", "write_file"],
        ).get_tools()
        return tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
Complete the first to-be-completed task on the checklist. And summarize what you did based on the original task.
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt


class DoAllChecklistAgent(DoChecklistAgent):
    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
Complete all tasks on the checklist. And summarize what you did based on the original task.
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt


class FormattedChecklistAgent(SimpleAgent):
    def __init__(self, plan: str) -> None:
        super().__init__()
        self.plan = plan

    @property
    def name(self):
        return "FormattedChecklist"

    def _get_memory(self):
        chat_history = [
            HumanMessage(content=f"Plan:\n{self.plan}"),
        ]
        return chat_history

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Acts like a formatting tool.Convert plan to checklist.
You can only use the CREATE, READ, MODIFY and DELETE keywords to make checklist.
## Example:
### INPUT
Plan:
1. Read the README.rst file to understand the goals of the project.
2. Open the main.py file and take a look at the files that need to be changed.
3. Update the README.rst file based on the new guidelines.
4. Make the necessary changes to the main.py file by adding the required functions.
### OUTPUT
Checklist:
- [ ] READ README.rst  # Understand project goals
- [ ] READ main.py  # View files to be modified
- [ ] MODIFY README.rst  # update README.rst due to changes in guidelines
- [ ] MODIFY main.py  # Add required functions
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )
        return prompt

    def run(self) -> str:
        output = super().run()
        data = f"Checklist:\n{output}"
        return data

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class FormattedQueryChecklistAgent(FormattedChecklistAgent):
    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Acts like a formatting tool.Convert plan to checklist.
You can only use the READ keywords to make checklist.
## Example:
### INPUT
Plan:
1. Read the README.rst file to understand the goals of the project.
2. Open the main.py file and take a look at the files that need to be changed.
### OUTPUT
Checklist:
- [ ] READ README.rst  # Understand project goals
- [ ] READ main.py  # View files to be modified
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )
        return prompt


class ReviewAgent(SimpleAgent):
    def __init__(
        self, checklist: str, result: str, user_review: str, do_all=False
    ) -> None:
        super().__init__()
        self.checklist = checklist
        self.user_review = user_review
        self.result = result
        self.do_all = do_all

    @property
    def name(self):
        return "UpdateChecklist"

    def _get_memory(self):
        chat_history = [
            AIMessage(content=f"{self.result}"),
            HumanMessage(content=f"{self.user_review}"),
            SystemMessage(
                content="""Guess whether the user's reply similar the following intentions:
Can continue the mission or current work is completed

You just need to answer Y/N
"""
            ),
        ]
        return chat_history

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                ("system", "{input}"),
            ]
        )
        return prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)

    def run(self) -> str:
        resp = super().run()
        update_checklist = self.checklist
        if resp.upper() == "Y":
            if self.do_all:
                return re.sub(r"- \[ \]", "- [x]", update_checklist)
            else:
                return re.sub(r"\[ \]", "[x]", update_checklist, count=1)

        return update_checklist
