import pytest
from unittest.mock import MagicMock

from devbot.repo.gitee import IssueEvent
from devbot.repo.gitserver import (
    GiteeServer,
    GitServerFactory,
)
import dotenv


def test_git_server_factory_create_gitee_server():
    dotenv.load_dotenv()
    factory = GitServerFactory()
    server = factory.create_gitee_server()
    assert isinstance(server, GiteeServer)


def test_git_server_factory_create_server_from_event_gitee():
    dotenv.load_dotenv()
    factory = GitServerFactory()
    event = MagicMock()
    server = factory.create_gitee_server()
    assert isinstance(server, GiteeServer)
