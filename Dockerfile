FROM python:3.8-slim

WORKDIR /app

COPY . ./

RUN pip install flask gunicorn requests google-cloud-storage google-cloud-speech

CMD gunicorn --bind :$PORT app:app --timeout 6000