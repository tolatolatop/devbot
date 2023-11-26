from __future__ import print_function
import os
from dataclasses import dataclass
from typing import Union, Dict, List

import pygitee
from pprint import pprint


@dataclass
class User:
    login: str


@dataclass
class Repository:
    full_name: str
    name: str
    owner: User
    clone_url: str


@dataclass
class WebhookPayload:
    repository: Repository
    sender: User


@dataclass
class AciontPayload(WebhookPayload):
    action: str


@dataclass
class Issue:
    title: str
    labels: List
    state: str
    comments: int
    number: Union[str, int]


@dataclass
class IssueEvent(AciontPayload):
    issue: Issue


@dataclass
class Pusher:
    name: str
    email: str


@dataclass
class PushEvent(WebhookPayload):
    ref: str
    before: str
    after: str
    pusher: Pusher


@dataclass
class PingEvent(WebhookPayload):
    hook: Dict
    hook_id: int


def create_gitee_api_client(access_token=os.environ["GITEE_ACCESS_TOKEN"]):
    # Configure API key authorization: access_token
    configuration = pygitee.Configuration()
    configuration.api_key["access_token"] = access_token

    # create an instance of the API class
    api_client = pygitee.ApiClient(configuration)
    return api_client


AllEvent = Union[IssueEvent, PingEvent, PushEvent]
