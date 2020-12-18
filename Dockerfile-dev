FROM python:3.7-buster

ENV APP_DIR=/app
WORKDIR $APP_DIR

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get update && \
    apt-get install -y wait-for-it gdal-bin postgis && \
    apt-get clean

COPY app/requirements.txt $APP_DIR/
RUN pip install -r requirements.txt
