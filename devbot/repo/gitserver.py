import abc
import os
import github
import pygitee
from typing import List

from devbot import repo


class User(abc.ABC):
    @abc.abstractproperty
    def login(self):
        pass


class DictUser(User):
    def __init__(self, data: dict) -> None:
        super().__init__()
        self.__data = data

    def login(self):
        return self.__data["login"]


class IssueComment:
    @abc.abstractproperty
    def body(self):
        pass

    @abc.abstractproperty
    def user(self):
        pass


class DictIssueComment:
    def __init__(self, data: dict) -> None:
        super().__init__()
        self.__data = data

    @property
    def user(self):
        return DictUser(self.__data["user"])

    @property
    def body(self):
        return self.__data["body"]


class Issue:
    @abc.abstractproperty
    def user(self):
        pass

    @abc.abstractproperty
    def body(self):
        pass

    @abc.abstractproperty
    def repository(self):
        pass

    @abc.abstractproperty
    def number(self):
        pass

    @abc.abstractmethod
    def create_comment(self, body: str):
        pass

    @abc.abstractmethod
    def get_comments(self) -> List[IssueComment]:
        pass


class DictIssue(Issue):
    def __init__(self, data: dict) -> None:
        super().__init__()
        self.__data = data

    @property
    def user(self):
        return self.__data["user"].get("login")

    @property
    def body(self):
        return self.__data["body"]

    @property
    def number(self):
        return self.__data["number"]


class DictPullRequest(DictIssue):
    pass


class Repo(abc.ABC):
    @abc.abstractproperty
    def full_name(self):
        pass

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def clone_url(self):
        pass

    @abc.abstractproperty
    def owner(self):
        pass

    @abc.abstractmethod
    def get_issue(self, number) -> Issue:
        pass

    @abc.abstractmethod
    def create_pull(self, base, head, title, body):
        pass


class DictRepo(Repo):
    def __init__(self, data: dict) -> None:
        self.__data = data

    @property
    def full_name(self):
        return self.__data["full_name"]

    @property
    def name(self):
        return self.__data["name"]

    @property
    def clone_url(self):
        return self.__data["html_url"]

    @property
    def owner(self) -> User:
        return DictUser(self.__data["owner"])


class GiteeIssue(DictIssue):
    def __init__(self, data: dict, cli: pygitee.ApiClient) -> None:
        super().__init__(data)
        self.__cli = cli

    def create_comment(self, body: str):
        cli = pygitee.CommentApi(self.__cli)
        data = cli.repos_owner_repo_issues_number_comments_post(
            self.repository.owner,
            self.repository.name,
            number=self.number,
            body=body,
        )

    def get_comments(self):
        cli = pygitee.CommentApi(self.__cli)
        data: List[dict] = cli.repos_owner_repo_issues_number_comments_get(
            self.repository.owner,
            self.repository.name,
            number=self.number,
        )  # type: ignore
        comments = [DictIssueComment(d) for d in data]
        return comments

    @property
    def repository(self):
        return GiteeRepo(self.__data["repository"], self.__cli)


class GiteeRepo(DictRepo):
    def __init__(self, data: dict, cli: pygitee.ApiClient) -> None:
        super().__init__(data)
        self.__cli = cli

    def get_issue(self, number) -> Issue:
        cli = pygitee.IssueApi(self.__cli)
        data: dict = cli.repos_owner_repo_issues_number_get(
            self.owner, self.name, number=number
        )  # type: ignore
        return GiteeIssue(data, self.__cli)

    def create_pull(self, base, head, title, body):
        cli = pygitee.RepoApi(self.__cli)
        data: dict = cli.repos_owner_repo_pulls_post(
            self.owner.login, self.repo
        )  # type: ignore
        return DictPullRequest(data)


class GitSever(abc.ABC):
    @abc.abstractmethod
    def get_user(self) -> User:
        pass

    @abc.abstractmethod
    def get_repo(self, full_name_or_id) -> Repo:
        pass


class GitHubServer(github.Github, GitSever):
    pass


class GiteeServer(GitSever):
    def __init__(self, access_token) -> None:
        super().__init__()
        configuration = pygitee.Configuration()
        configuration.api_key["access_token"] = access_token

        # create an instance of the API class
        api_client = pygitee.ApiClient(configuration)
        self.__api_client = api_client

    def get_user(self):
        cli = pygitee.UserApi(self.__api_client)
        data: dict = cli.user_get()  # type: ignore
        return DictUser(data)

    def get_repo(self, full_name_or_id) -> Repo:
        cli = pygitee.RepoApi(self.__api_client)
        tmp = full_name_or_id.split("/")
        owner, repo = tmp[0], "/".join(tmp[1:])
        data: dict = cli.repos_owner_repo_get(owner=owner, repo=repo)  # type: ignore
        return super().get_repo(full_name_or_id)


class GitServerFactory:
    def create_server_from_event(self, event) -> GitSever:
        if isinstance(event, repo.github.IssueEvent):
            return self.create_github_server()
        else:
            return self.create_gitee_server()

    def create_github_server(self) -> GitHubServer:
        auth = github.Auth.Token(os.environ["GITHUB_TOKEN"])
        g = GitHubServer(auth=auth)
        return g

    def create_gitee_server(self):
        access_token = os.environ["GITEE_ACCESS_TOKEN"]
        return GiteeServer(access_token)
