import pytest
from langchain.schema.messages import HumanMessage, SystemMessage, AIMessage


from unittest import mock


read_file = [
    {
        "repo_url": "https://github.com/tolatolatop/devbot",
        "issue_number": 15,
    }
]


def read_file_memory():
    memory = [
        SystemMessage(
            content="filelist:\nDockerfile\n.env.template\nREADME.rst\n---\n"
        ),
        HumanMessage(content="解释项目中所有需要配置的环境变量"),
    ]
    return mock.Mock(return_value=memory)


def list_file_memory():
    memory = [
        HumanMessage(content="请使用list_directory函数获取仓库文件列表"),
    ]
    return mock.Mock(return_value=memory)


memory_tasks = [
    pytest.param(read_file_memory(), "LANGCHAIN_TRACING_V2"),
    pytest.param(
        list_file_memory(),
        ".env.templates",
        marks=pytest.mark.skip("no tests"),
    ),
]

coding_chat_history = [
    HumanMessage(content="README.rst中缺少项目环境变量描述，请根据仓库内容添加信息"),
    AIMessage(
        content="""
- [ ] READ README.rst: Understand the current content of the file.
- [ ] READ .env.template: Get the list of project environment variables.
"""
    ),
    HumanMessage(content="Complete information collection plan"),
    AIMessage(
        content="""
Task Info:
- LANGCHAIN_TRACING_V2=true
- LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
- LANGCHAIN_API_KEY=<your-api-key>
- LANGCHAIN_PROJECT=<your-project> (defaults to "default" if not specified)
- OPENAI_API_KEY=<your-openai-api-key>
- SMEE_SOURCE=https://smee.io/new
- SMEE_TARGET=http://devbot:8000/webhook/github
Is there anything specific you would like to extract from this information?
"""
    ),
    HumanMessage(content="根据获取到的信息生成coding checklist"),
    AIMessage(
        content="""
ToDo:
- [ ] Modify the README.rst file to include the following project environment variable descriptions:
"""
    ),
    HumanMessage(content="完成ToDo Checklist"),
    AIMessage(
        content="""
Here is the updated ToDo checklist:

- [x] Modify the README.rst file to include the following project environment variable descriptions:
  - LANGCHAIN_TRACING_V2=true
  - LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
  - LANGCHAIN_API_KEY=<your-api-key>
  - LANGCHAIN_PROJECT=<your-project> (defaults to "default" if not specified)
  - OPENAI_API_KEY=<your-openai-api-key>
  - SMEE_SOURCE=https://smee.io/new
  - SMEE_TARGET=http://devbot:8000/webhook/github
"""
    ),
]

checklist_chat_history = [
    SystemMessage(
        content="""
Checklist:
- [x] Say Hello
- [ ] Calculate
- [ ] Choice One Word
- [ ] Say Goodbay
"""
    ),
    AIMessage(
        content="""
FINISHED: Calculate
"""
    ),
]

checklist_agent_tasks = [
    pytest.param(
        mock.Mock(
            return_value=checklist_chat_history + [HumanMessage(content="通过")]
        ),
        2,
        id="ok",
    ),
    pytest.param(
        mock.Mock(
            return_value=checklist_chat_history
            + [HumanMessage(content="重新检查一下")]
        ),
        3,
        id="recheck",
    ),
    pytest.param(
        mock.Mock(
            return_value=checklist_chat_history + [HumanMessage(content="不行")]
        ),
        3,
        id="redo",
    ),
    pytest.param(
        mock.Mock(
            return_value=checklist_chat_history + [HumanMessage(content="下一步")]
        ),
        2,
        id="next",
    ),
]

coding_plan_tasks = [
    pytest.param(
        mock.Mock(return_value=coding_chat_history[:1]),
        "[ ] READ",
        id="collect info",
    ),
    pytest.param(
        mock.Mock(return_value=coding_chat_history[3:5]),
        "[ ] MODIFY",
        id="create todo",
    ),
]

coding_tasks = [
    pytest.param(
        mock.Mock(return_value=coding_chat_history[:3]),
        "LANGCHAIN_TRACING_V2",
        id="read info",
        marks=pytest.mark.skip("no test"),
    ),
    pytest.param(
        mock.Mock(return_value=coding_chat_history[3:7]),
        "README.rst",
        id="do task",
    ),
]

write_tasks = [
    pytest.param(
        "README.rst",
        """
| Variable Name       | Value                                 |
|---------------------|---------------------------------------|
| LANGCHAIN_TRACING_V2 | true                                  |
| LANGCHAIN_ENDPOINT  | https://api.smith.langchain.com        |
| LANGCHAIN_API_KEY   | <your-api-key>                        |
| LANGCHAIN_PROJECT   | <your-project> (if not specified, defaults to "default") |
| OPENAI_API_KEY      | <your-openai-api-key>                 |
| SMEE_SOURCE         | https://smee.io/new                    |
| SMEE_TARGET         | http://devbot:8000/webhook/github       |
""",
        "为原始文件补充环境变量设置",
        id="env",
    ),
]

plan_tasks = [
    pytest.param(
        "新增一个fastapi接口, 返回 a + b的值",
    ),
]

do_plan_tasks = [
    pytest.param(
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] READ cli.py  # Check if there are any existing API endpoints and understand the code structure
""",
        "No helpful information.",
        marks=pytest.mark.skip("pass"),
        id="cli",
    ),
    pytest.param(
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] READ devbot/devbot.py  # Check if there are any existing API endpoints and understand the code structure
""",
        "a + b",
        marks=pytest.mark.skip("pass"),
        id="devbot/devbot",
    ),
    pytest.param(
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] READ tests/test_devbot.py  # Check if the required ce already exists
""",
        "No helpful information",
        id="tests/test_devbot",
    ),
]

plan_to_do_task_info = """
Based on the provided code, there are already existing API endpoints defined in the `devbot/devbot.py` file. 

To add a new FastAPI endpoint that returns the sum of two numbers `a` and `b`, you can modify the code as follows:

```python
@app.get("/sum/{a}/{b}")
async def sum_numbers(a: int, b: int):
    return {"result": a + b}
```
"""

plan_to_do_tasks = [
    pytest.param(
        "新增一个fastapi接口, 返回 a + b 的值",
        plan_to_do_task_info,
        id="sum a + b",
    ),
]

to_do_tasks = [
    pytest.param(
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] MODIFY devbot/devbot.py  # Add a new FastAPI endpoint for summing numbers
""",
        plan_to_do_task_info,
        id="sum a + b",
    ),
]
