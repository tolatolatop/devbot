from devbot.agent.base import DevAgent


from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage


from typing import Callable, Dict, Tuple


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
