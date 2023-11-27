import os

from github import Github
from github import Auth

from devbot.repo import gitserver


def accept_event(event):
    g = gitserver.GitServerFactory().create_server_from_event(event)
    if g:
        if event.sender.login != g.get_user().login:
            return g
        else:
            return None
    return g
