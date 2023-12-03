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
