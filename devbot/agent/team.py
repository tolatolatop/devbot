import re
import abc
from typing import Optional, Type, Any, Dict, Tuple, Callable

from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.memory import ConversationBufferMemory
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.pydantic_v1 import BaseModel, Field
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.tools.base import BaseTool

from devbot.agent.base import DevAgent, SimpleAgent
from devbot.agent.tools import GitToolkit


class CallInput(BaseModel):
    """Input for CallTool"""

    name: str = Field(..., description="the person you want to call")
    message: str = Field(..., description="the message you want to convey")


class CallToolMixin(BaseModel):
    call_list: Dict[str, Any] = {}

    def get_call(self, name: str) -> Any:
        if name in self.call_list:
            return self.call_list[name]
        raise ValueError("The called user cannot be found")


class CallTool(CallToolMixin, BaseTool):
    """Tool that call someone who can solve the problem."""

    name: str = "call_one"
    args_schema: Type[BaseModel] = CallInput
    description: str = "Tool that call someone who can solve the problem"

    def _run(
        self,
        name: str,
        message: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            agent = self.get_call(name)
            return agent.run({"input": message})
        except Exception as e:
            return "Error: " + str(e)


class RoleAgentMixin(abc.ABC):
    @property
    @abc.abstractmethod
    def role(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass


class CallerAgent(RoleAgentMixin, DevAgent):
    def __init__(self) -> None:
        super().__init__()
        self._memory = ConversationBufferMemory(
            return_messages=True, output_key="output", input_key="input"
        )
        self._current_question = {}
        self._phone_book = {}

    @property
    def phone_book(self) -> Dict[str, RoleAgentMixin]:
        return self._phone_book

    @property
    def phone_book_str(self) -> str:
        result = ""
        if len(self.phone_book) == 0:
            return "Noboy you can call."
        for agent in self.phone_book.values():
            result += f"{agent.name}: {agent.role}\n"
        return result

    def _get_tools(self):
        tools = [CallTool(call_list=self.phone_book)]
        return tools

    def _get_memory(self):
        return self._memory.load_memory_variables({})["history"]

    def _get_inputs(self) -> Tuple[str, Dict[str, Callable]]:
        chat_history = self._get_memory()
        input = HumanMessage(content=self._current_question["input"])
        data = {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
            "chat_history": lambda x: x.get("chat_history") or chat_history,
        }
        return input, data  # type: ignore

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"This is a calling list, you can only call the people on it.\n{self.phone_book_str}",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt

    def run(self, input: Dict[str, str]) -> str:
        self._current_question.update(input)
        resp = super().run()
        self._memory.save_context(input, {"output": resp})
        return resp


class ProjectAgent(SimpleAgent):
    def __init__(self, code_dir) -> None:
        super().__init__()
        self.code_dir = code_dir

    def _get_project_info(self):
        git_toolkit = GitToolkit(root_dir=self.code_dir)
        tools = git_toolkit.get_tools()
        tool = [t for t in tools if t.name == "list_directory"][0]
        files_list = tool.run({})
        return SystemMessage(content=f"file list in project:\n {files_list}")

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class CoderAgent(ProjectAgent, CallerAgent):
    @property
    def name(self) -> str:
        return "Coder"

    @property
    def role(self) -> str:
        return (
            "Have access to view the code and answer questions about the repos"
        )

    def _get_tools(self):
        tools = [
            CallTool(call_list=self.phone_book),
        ]
        fs_tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()
        return tools + fs_tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""You are very powerful coding assistant."
Please complete the request from the user.
This is a calling list, you can only call the people on it.\n{self.phone_book_str}""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt


class IssueAgent(ProjectAgent, CallerAgent):
    @property
    def name(self) -> str:
        return "Issue"

    @property
    def role(self) -> str:
        return "Can communicate directly with users"

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are very powerful coding assistant. Please answer the question based on the actual contents of repo. But you don’t know anything about the repository.

This is a calling list, when you encounter a problem you don’t know about, you can call them to help you.
Calld List:
Coder: Have access to view the code and answer questions about the repos
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt
