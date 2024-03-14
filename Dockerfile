FROM python:3.8-slim-buster

WORKDIR /app

RUN apt-get update && apt-get upgrade --allow-unauthenticated -y

COPY requirements.txt requirements.txt

RUN pip3 install -U pip

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "run.py" ]
