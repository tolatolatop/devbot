from devbot.agent.base import DevAgent


from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage


from typing import Callable, Dict, Tuple

from devbot.agent.tools import GitToolkit


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
            HumanMessage(content=f"Append content:\n{self.text}"),
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


class PlanAgent(DevAgent):
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


class PlanQueryAgent(PlanAgent):
    @property
    def name(self):
        return "Plan"

    def _get_memory(self):
        chat_history = [
            self._get_project_info(),
            HumanMessage(content=f"{self.task}"),
        ]
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["copy_file"],
        ).get_tools()
        return tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are very powerful coding assistant.Collect relevant information as required.Develop a plan for collecting information based on the user's tasks.
You can only use the READ keywords to develop your plan. Your plan contains up to 5 checklists.

Correct Example:
- [ ] READ README.rst  # Understand project goals
- [ ] READ main.py  # View files to be modified
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "Task is: {input}. "),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt


class PlanToDoAgent(PlanAgent):
    def __init__(self, code_dir, task: str, task_info: str) -> None:
        super().__init__(code_dir=code_dir, task=task)
        self.task_info = task_info

    @property
    def name(self):
        return "PlanToDo"

    def _get_memory(self):
        chat_history = [
            self._get_project_info(),
            HumanMessage(
                content=f"""
{self.task}
task_info:
{self.task_info}
Be careful not to forget to add a plan for tests.
"""
            ),
        ]
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()
        return tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are very powerful coding assistant. Generates an execution plan based on the provided information and user requirements.
You can only use the CREATE, MODIFY, and DELETE keywords to make plans. Your plan contains up to 5 checklists.
## Correct Example:
- [ ] MODIFY README.rst  # update README.rst due to changes in guidelines
- [ ] MODIFY main.py  # Add required functions
- [ ] MODIFY test_main.py  # Test new required functions
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "user",
                    "Original Task Desc: {input}.",
                ),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt


class DoPlanAgent(DevAgent):
    def __init__(self, code_dir, task: str, plan: str) -> None:
        super().__init__()
        self.code_dir = code_dir
        self.task = task
        self.plan = plan

    @property
    def name(self):
        return "DoPlan"

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()
        return tools

    def _get_memory(self):
        chat_history = [
            HumanMessage(content=f"Plan:\n{self.plan}"),
            HumanMessage(content=f"{self.task}"),
        ]
        return chat_history

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are very powerful coding assistant.
Complete the information gathering plan by following these steps:
1. Obtain original information based on plan
2. Extract information related to user requirements
If there is nothing task-relevant in the original message. will return "No helpful information"
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "Task: {input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class ToDoAgent(DoPlanAgent):
    def __init__(self, code_dir, task: str, plan: str, task_info: str) -> None:
        super().__init__(code_dir, task, plan)
        self.task_info = task_info

    @property
    def name(self):
        return "ToDo"

    def _get_memory(self):
        chat_history = [
            HumanMessage(
                content=f"Origin Task:\n{self.task}\n Task Info:\n {self.task_info}"
            ),
            HumanMessage(content=f"{self.plan}"),
        ]
        return chat_history

    def _get_tools(self):
        from devbot.agent.toolkit import WriteFileTool

        tools = [WriteFileTool(root_dir=self.code_dir)]
        return tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are very powerful coding assistant. Use tools to complete ToDo.
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "ToDo:\n{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt
