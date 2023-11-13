import os

from langchain.chat_models import ChatOpenAI
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from github import Github
from github import Auth

import tools
import prompts


def create_agent_executor(
    repo_name: str, repo_url: str, commit_id: str, issue_number: int
):
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth)
    root_path = tools.prepare_env(repo_url, repo_name, commit_id)
    chat_history = tools.create_issue_chat_history(g, repo_name, issue_number)
    tools_list = tools.create_filesystem_tools(root_path) + []
    use_prompt = prompts.coding_prompt

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
            "chat_history": lambda x: x.get("chat_history")
            or chat_history[:-1],
        }
        | use_prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    ).with_config(run_name="Agent")

    agent_executor = AgentExecutor(agent=agent, tools=tools_list)
    agent_executor.invoke({"input": chat_history[-1].content})
    return agent_executor


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    repo_name = "tolatolatop/devbot"
    repo_url = f"https://github.com/{repo_name}"
    commit_id = "master"
    issue_number = 13
    ae = create_agent_executor(repo_name, repo_url, commit_id, issue_number)
