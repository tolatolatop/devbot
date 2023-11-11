FROM python:3.9

WORKDIR app

COPY poetry.lock pyproject.toml .

RUN pip install pipx && pipx install poetry && ln -s /root/.local/bin/poetry /usr/local/bin
RUN poetry install --only main

COPY devbot devbot

CMD ["poetry", "run", "uvicorn", "devbot.devbot:app", "--host", "0.0.0.0", "--port", "80", "--log-config=devbot/log_conf.yaml"]