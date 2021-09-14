FROM python:3.8-slim-buster
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /project/application

ENV SHELL /bin/bash

WORKDIR /project

RUN apt-get update && apt-get install -y \
    gettext \
    git \
    gcc \
&& apt-get clean

RUN pip install -U \
    pip \
    setuptools \
    wheel

COPY . .

RUN pip install -r requirements.txt

CMD python prebooru.py server
