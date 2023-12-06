from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from devbot.agent.base import SimpleAgent
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage


class GenChecklistAgent:
    pass


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
