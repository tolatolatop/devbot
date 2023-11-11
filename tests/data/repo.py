webhook_test_data = [
    {
        "action": "opened",
        "repository": {
            "full_name": "username/repository",
            "name": "repository",
            "owner": {"login": "username"},
        },
        "sender": {"login": "username"},
        "issue": {
            "url": "https://github.com/username/repository/issues/1",
            "repository_url": "https://github.com/username/repository",
            "comments_url": "https://github.com/username/repository/issues/1/comments",
            "title": "Example Issue",
            "labels": ["bug"],
            "state": "open",
            "comments": "This is an example issue.",
        },
    },
    {
        "action": "ping",
        "repository": {
            "full_name": "username/repository",
            "name": "repository",
            "owner": {"login": "username"},
        },
        "sender": {"login": "username"},
        "hook": {"id": 123456},
        "hook_id": 123456,
    },
    {
        "action": "pushed",
        "repository": {
            "full_name": "username/repository",
            "name": "repository",
            "owner": {"login": "username"},
        },
        "sender": {"login": "username"},
        "ref": "refs/heads/main",
        "before": "abcdef12345",
        "after": "12345abcdef",
        "pusher": {"login": "username"},
    },
]
