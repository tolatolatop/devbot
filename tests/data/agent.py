import pytest
from langchain.schema.messages import HumanMessage, SystemMessage


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

update_env_var_to_readme = [
    HumanMessage(
        content="""
1.读取项目中.env.template文件
2.根据读取到的内容进行总结
3.将总结的内容以表格形式增加到到项目README.rst，注意再写入前先读取README.rst的内容
4.最后读取最终README.rst内容并返回
"""
    ),
]

coding_tasks = [
    pytest.param(
        mock.Mock(return_value=update_env_var_to_readme),
        "LANGCHAIN_TRACING_V2",
        id="env write",
    ),
]

write_tasks = [
    pytest.param(
        ".agent_cache/tolatolatop/devbot@master@15",
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
        ".agent_cache/tolatolatop/devbot@master@15",
        "新增一个fastapi接口, 返回 a + b的值",
    ),
]

do_plan_tasks = [
    pytest.param(
        ".agent_cache/tolatolatop/devbot@master@15",
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] READ cli.py  # Check if there are any existing API endpoints and understand the code structure
""",
        "No helpful information.",
        marks=pytest.mark.skip("pass"),
        id="cli",
    ),
    pytest.param(
        ".agent_cache/tolatolatop/devbot@master@15",
        "新增一个fastapi接口, 返回 a + b 的值",
        """
- [ ] READ devbot/devbot.py  # Check if there are any existing API endpoints and understand the code structure
""",
        "a + b",
        marks=pytest.mark.skip("pass"),
        id="devbot/devbot",
    ),
    pytest.param(
        ".agent_cache/tolatolatop/devbot@master@15",
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

This new endpoint will be accessible at `/sum/{a}/{b}` where `{a}` and `{b}` are the numbers you want to add. For example, if you want to add 3 and 5, you can make a GET request to `/sum/3/5` and it will return `{"result": 8}`.
"""

plan_to_do_tasks = [
    pytest.param(
        ".agent_cache/tolatolatop/devbot@master@15",
        "新增一个fastapi接口, 返回 a + b 的值",
        plan_to_do_task_info,
        id="sum a + b",
    ),
]
