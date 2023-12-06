from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from devbot.agent.base import SimpleAgent


class GenChecklistAgent:
    pass


class DoChecklistAgent:
    pass


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
