from dataclasses import dataclass
from typing import Union, Dict, List


@dataclass
class User:
    login: str


@dataclass
class Repository:
    full_name: str
    name: str
    owner: User


@dataclass
class WebhookPayload:
    action: str
    repository: Repository
    sender: User


@dataclass
class Issue:
    url: str
    repository_url: str
    comments_url: str
    title: str
    labels: List
    state: str
    comments: str


@dataclass
class IssueEvent(WebhookPayload):
    issue: Issue


@dataclass
class PushEvent(WebhookPayload):
    ref: str
    before: str
    after: str
    pusher: User


@dataclass
class PingEvent(WebhookPayload):
    hook: Dict
    hook_id: int


AllEvent = Union[IssueEvent, PingEvent, PushEvent]
