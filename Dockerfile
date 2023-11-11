FROM python:3.9

WORKDIR app

COPY requirements.txt .
RUN pip install -r requirements.txt --progress-bar off

COPY devbot .

CMD ['uvicorn', 'devbot:app', '--host', '0.0.0.0', '--port', '80']