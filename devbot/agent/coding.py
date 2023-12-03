import os
import github
from git import Repo


from langchain.agents.agent_toolkits import FileManagementToolkit
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage

from devbot.agent.base import DevAgent
from devbot.agent.tools import GitToolkit
from devbot.agent import toolkit


class IssueAgent(DevAgent):
    def __init__(self, git_server: github.Github, repo_url: str, issue_number):
        self.git_server = git_server
        self.repo_name = self.get_repo_name_from_url(repo_url)
        self.issue_number = issue_number
        self.code_dir = self.prepare_env(repo_url)

    @staticmethod
    def get_repo_name_from_url(repo_url):
        host = "https://github.com/"
        return repo_url[len(host) :]

    def prepare_env(self, repo_url: str, commit_id: str = "master") -> str:
        local_dir = (
            f"./.agent_cache/{self.repo_name}@{commit_id}@{self.issue_number}"
        )
        if os.path.isdir(local_dir):
            repo = Repo(local_dir)
            repo.remotes.origin.pull()
        else:
            repo = Repo.clone_from(repo_url, local_dir)
        return local_dir

    @property
    def name(self):
        return "Issue"

    def _get_issue_chat_history(self):
        repo = self.git_server.get_repo(self.repo_name)
        ai_user = self.git_server.get_user().login
        issue = repo.get_issue(number=self.issue_number)
        chat_history = []
        if issue.user == ai_user:
            msg = AIMessage(content=issue.body)
        else:
            msg = HumanMessage(content=issue.body)
        chat_history.append(msg)
        for c in issue.get_comments():
            if c.user.login == ai_user:
                msg = AIMessage(content=c.body)
            else:
                msg = HumanMessage(content=c.body)
            chat_history.append(msg)
        return chat_history

    def _get_project_info(self):
        git_toolkit = GitToolkit(root_dir=self.code_dir)
        tools = git_toolkit.get_tools()
        tool = [t for t in tools if t.name == "list_directory"][0]
        files_list = tool.run({})
        return SystemMessage(content=f"file list: {files_list}")

    def _get_memory(self):
        chat_history = self._get_issue_chat_history()
        project_info = self._get_project_info()
        chat_history.insert(0, project_info)
        return chat_history

    def _get_tools(self):
        tools = FileManagementToolkit(
            root_dir=str(self.code_dir),
            selected_tools=["read_file"],
        ).get_tools()
        return tools

    def _get_prompt(self):
        issue_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are very powerful coding assistant."
                    "Please answer the question based on the actual contents of repo."
                    "You are allowed to use tools to view "
                    "the repository and specific files",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return issue_prompt

    def _get_chat_model(self):
        return ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


class CodingAgent(IssueAgent):
    def _get_tools(self):
        tools = [
            # toolkit.InfoPlanTool(root_dir=self.code_dir),
            # toolkit.DoInfoPlanTool(root_dir=self.code_dir),
            toolkit.ToDoPlanTool(root_dir=self.code_dir),
        ]
        return tools

    def _get_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a very good programming expert. Please follow the process below to resolve the issue.
1. According to the user's needs, generate information collection plan. Return information collection Checklist.
2. Complete information collection Checklist. Return helpful information.
3. Use ToDoPlan to generate a coding plan based on the user's needs.  Return results using Checklist.
4. Complete the ToDo according to the user's needs. Return task related complete information
Stop waiting for user instructions when completing each process.
""",
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        return prompt
