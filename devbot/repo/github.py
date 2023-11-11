from dataclasses import dataclass
from typing import Union, Dict


@dataclass
class WebhookPayload:
    action: str
    repository: Dict
    sender: Dict


@dataclass
class IssueEvent(WebhookPayload):
    issue: Dict


@dataclass
class PingEvent(WebhookPayload):
    hook: Dict
    hook_id: int


AllEvent = Union[IssueEvent, PingEvent]
