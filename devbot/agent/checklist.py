from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage

from devbot.agent.tools import GitToolkit
from devbot.agent.base import SimpleAgent


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


class DoChecklistAgent:
    pass


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


class MetaChecklistAgent(SimpleAgent):
    @property
    def name(self):
        return "Checklist"

    def _get_memory(self):
        chat_history = []
        return chat_history

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
There is a Checklist table here. The Checklist table is updated based on the user's answers. You need to return it in the original format.`
If the checklist has been completed, returns that "all tasks have been completed"
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
            ]
        )
        return prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
