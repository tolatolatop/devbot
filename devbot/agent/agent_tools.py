from git import Repo
import os
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools.render import format_tool_to_openai_function
from langchain.schema.messages import HumanMessage, AIMessage, FunctionMessage

from github import Github
from github import Auth

import tools
import prompts
from tools import create_filesystem_tools


def prepare_coding_agent(root_path):
    chat_history = []
    tools_list = tools.create_filesystem_tools(
        root_path
    ) + create_coding_tools(root_path)
    prompt = prompts.coding_prompt
    return prompt, tools_list, chat_history


def create_coding_agent_executor(use_prompt, tools_list, chat_history):
    llm = ChatOpenAI(temperature=0)
    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(t) for t in tools_list]
    )

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
            "chat_history": lambda x: x.get("chat_history") or chat_history,
        }
        | use_prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    ).with_config(run_name="Coding Agent")

    agent_executor = AgentExecutor(agent=agent, tools=tools_list)
    return agent_executor


def create_coding_tools(root_path):
    @tool
    def update_file(file_path: str, content: str):
        """Modify file content.Must input new content in one line"""
        repo = Repo(root_path)

        r_file_path = os.path.join(root_path, file_path)
        with open(r_file_path, "w") as file:
            file.write(content)

        repo.git.add(file_path)
        return f"update {file_path} ok!"

    @tool
    def commit_task(commit_message: str):
        """Record changes to the repository"""
        repo = Repo(root_path)
        commit_id = repo.git.commit("-m", commit_message, "-s")
        return f"commit changes ok!"

    @tool
    def create_pull_request(pr_title: str, pr_body: str):
        """Create a pull request"""
        repo = Repo(root_path)
        pr_title = "Add License"
        pr_body = "Please merge this PR to add the MIT License."
        # 缺少token环境
        repo.git.execute(
            ["gh", "pr", "create", "--title", pr_title, "--body", pr_body]
        )
        return f"create pr ok!"

    return [update_file, commit_task, create_pull_request]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    root_path = "/workspaces/devbot"
    prompt, tools_list, chat_history = prepare_coding_agent(root_path)
    ae = create_coding_agent_executor(prompt, tools_list, chat_history)
    task = """
devbot/agent/tools.py:16:1: F401 'prompts' imported but unused
devbot/agent/tools.py:97:5: F841 local variable 'root_dir' is assigned to but never used
"""
    resp = ae.invoke({"input": "Please fix the following issues." + task})
    print(resp["output"])
