#!/bin/bash

gh auth login --hostname GitHub.com
gh auth setup-git
poetry run uvicorn devbot.devbot:app --host 0.0.0.0 --log-config=devbot/log_conf.yaml