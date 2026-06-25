# docker/Dockerfile

FROM python:3.11-slim

WORKDIR /sandbox

RUN pip install pytest coverage bandit pylint

COPY requirements.txt .
RUN pip install -r requirements.txt