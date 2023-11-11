FROM python:3.9

WORKDIR app

COPY requirements_dev.txt .
RUN pip install -r requirements_dev.txt

COPY devbot .

CMD ['uvicorn', 'devbot:app', '--host', '0.0.0.0', '--port', '80']