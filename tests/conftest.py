import pytest
import os
from dotenv import load_dotenv, find_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    env_file = find_dotenv(".env")
    load_dotenv(env_file)


@pytest.fixture
def git_server():
    import github

    auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    g = github.Github(auth=auth)
    return g
