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
    repository: Repository
    sender: User


@dataclass
class AciontPayload(WebhookPayload):
    action: str


@dataclass
class Issue:
    url: str
    repository_url: str
    comments_url: str
    title: str
    labels: List
    state: str
    comments: int


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


AllEvent = Union[IssueEvent, PingEvent, PushEvent]
