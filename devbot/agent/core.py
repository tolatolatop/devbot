from langchain.chat_models import ChatOpenAI
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

import tools
import prompts

from dotenv import load_dotenv

load_dotenv()

repo_name = "tolatolatop/devbot"
repo_url = f"https://github.com/{repo_name}"
commit_id = "master"
root_path = tools.prepare_env(repo_url, repo_name, commit_id)
tools = tools.create_filesystem_tools(root_path) + []
use_prompt = prompts.coding_prompt

llm = ChatOpenAI(temperature=0)
llm_with_tools = llm.bind(
    functions=[format_tool_to_openai_function(t) for t in tools]
)


agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_functions(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x.get("chat_history") or [],
    }
    | use_prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
).with_config(run_name="Agent")


agent_executor = AgentExecutor(agent=agent, tools=tools)

agent_executor.invoke(
    {"input": "Explain all environment variables that need to be set."}
)
