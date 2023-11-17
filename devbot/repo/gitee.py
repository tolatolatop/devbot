import os

from dataclasses import dataclass
from requests import Session
from requests.models import PreparedRequest


@dataclass
class User:
    login: str


@dataclass
class IssueData:
    title: str
    number: str


@dataclass
class IssueComment:
    body: str
    user: User


class OAuth:
    site = "https://gitee.com/oauth"

    def __init__(self):
        self.__client_id = os.environ.get('GITEE_CLIENT_ID')
        self.__redirect_uri = os.environ.get('GITEE_APP_REDIRECT_URL')
        self.__client_secret = os.environ.get("GITEE_CLIENT_SECRET")
        self.__is_authorized = os.environ.get("GITEE_CLIENT_SECRET") == "yes"
        self.__scope = "user_info pull_requests issues notes projects"

    def get_oauth_url(self):
        api_path = "/authorize"
        params = {
            "client_id": self.__client_id,
            "redirect_uri": self.__redirect_uri,
            "response_type": "code"
        }
        if self.__is_authorized:
            params['scope'] = self.__scope
        url = self.site + api_path
        req = PreparedRequest()
        req.prepare_url(url, params)
        return req.url

    def get_access_token_req(self, code):
        api_path = "token"
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.__client_id,
            "redirect_uri": self.__redirect_uri,
        }
        url = self.site + api_path
        req = PreparedRequest()
        req.prepare_url(url, params)
        data = {
            "client_secret": self.__client_secret
        }
        return "POST", req.url, data

    def get_access_token_req_password(self, username, password):
        api_path = "/token"
        params = {
            "grant_type": "password",
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "username": username,
            "password": password,
            "scope": self.__scope
        }
        url = self.site + api_path
        return "POST", url, params


class Gitee:
    site = "https://gitee.com/api/v5"

    def __init__(self):
        self.__session = Session()
        self.auth_body = {}

    def __get_access_token(self, username, password):
        access_token = os.environ.get('GITEE_ACCESS_TOKEN')
        if access_token:
            return access_token
        oauth = OAuth()
        method, url, data = oauth.get_access_token_req_password(username, password)
        resp = self.__session.request(method, url, json=data)
        return resp.json()['access_token']

    def auth(self, username, password):
        resp = self.__get_access_token(username, password)
        print(resp)
        self.auth_body['access_token'] = resp

    def requests(self, method, api_path, **kwargs):
        api_url = self.site + api_path
        query_params = self.auth_body.copy()
        if kwargs.get('params'):
            query_params.update(kwargs.get('params'))
        return self.__session.request(method, api_url, params=query_params, **kwargs)

    def get_user(self):
        api_path = "/user"
        data = self.requests("GET", api_path).json()
        return User(login=data['login'])

    def get_repo(self, repo_name):
        api_path = f"/repos/{repo_name}"
        data = self.requests("GET", api_path).json()
        return Repo(data, self)


class Repo:

    def __init__(self, repo_data, gitee: Gitee):
        self.__gitee = gitee
        self.__data = repo_data

    @property
    def full_name(self):
        return self.__data['full_name']

    @property
    def name(self):
        return self.__data['name']

    @property
    def clone_url(self):
        return self.__data['html_url']

    def get_issue(self, number):
        api_path = f"/repos/{self.full_name}/issues/{number}"
        resp = self.__gitee.requests("GET", api_path)
        return Issue(resp.json(), self, self.__gitee)


class Issue:

    def __init__(self, data, repo: Repo, gitee: Gitee):
        self.__repo = repo
        self.__gitee = gitee
        self.data = data
        self.__issue_id = data['number']

    @property
    def user(self):
        return self.data['user'].get('login')

    @property
    def body(self):
        return self.data['body']

    def create_comment(self, body: str):
        api_path = f'/repos/{self.__repo.full_name}/issues/{self.__issue_id}/comments'
        params = {
            'body': body
        }
        resp = self.__gitee.requests("POST", api_path, json=params)
        return resp

    def get_comments(self):
        api_path = f"/repos/{self.__repo.full_name}/issues/{self.__issue_id}/comments"
        resp = self.__gitee.requests("GET", api_path)
        data = [
            IssueComment(
                body=d.get('body'),
                user=User(
                    login=d.get('user').get('login')
                )
            ) for d in resp.json()
        ]
        return data


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    app = Gitee()
    u, p = os.environ.get('GITEE_BOT_USR'), os.environ.get('GITEE_BOT_PSW')
    app.auth(u, p)
    test_repo_name = "ZekangZhou/devfastapi"
    repo = app.get_repo(test_repo_name)
    print(repo.clone_url)
    test_issue = 'I8HDEL'
    issue = repo.get_issue(test_issue)
    comments = issue.get_comments()
