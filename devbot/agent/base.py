import abc
from typing import List, Callable, Dict, Tuple

from langchain.chat_models.base import BaseChatModel
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.tools import BaseTool
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from langchain.tools.base import BaseTool


class DevAgent(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def _get_memory(self) -> List:
        pass

    @abc.abstractmethod
    def _get_tools(self) -> List[BaseTool]:
        pass

    @abc.abstractmethod
    def _get_prompt(self) -> ChatPromptTemplate:
        pass

    @abc.abstractmethod
    def _get_chat_model(self) -> BaseChatModel:
        pass

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

    def _run(self) -> str:
        llm = self._get_chat_model()
        tools = self._get_tools()
        tool_functions = [
            format_tool_to_openai_function(t) for t in self._get_tools()
        ]
        llm_with_tools = llm.bind(functions=tool_functions)

        input, inputs = self._get_inputs()

        use_prompt = self._get_prompt()
        agent = (
            inputs
            | use_prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        ).with_config(run_name=self.name)

        agent_executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True)  # type: ignore
        resp = agent_executor.invoke({"input": input.content})  # type: ignore
        return resp["output"]

    def run(self) -> str:
        return self._run()

    # TODO: Add aiofiles method
