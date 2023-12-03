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
    ),
]
