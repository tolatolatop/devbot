FROM python:3.9 as base

WORKDIR /app

RUN pip install pipx && pipx install poetry && ln -s /root/.local/bin/poetry /usr/local/bin
RUN type -p curl >/dev/null || ( apt update && apt install curl -y )
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install gh -y

RUN apt update && apt install docker.io -y

COPY poetry.lock pyproject.toml ./

FROM base as deploy
RUN poetry install --only main
COPY devbot devbot

CMD ["poetry", "run", "uvicorn", "devbot.devbot:app", "--host", "0.0.0.0", "--port", "80", "--log-config=devbot/log_conf.yaml"]

FROM base as dev
RUN poetry install
COPY . .

CMD ["bash"]