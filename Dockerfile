FROM python:3.7-buster

ENV APP_DIR=/app
WORKDIR $APP_DIR

RUN apt-get update && \
    apt-get install -y wait-for-it gdal-bin postgis && \
    apt-get clean

COPY app/requirements.txt $APP_DIR/
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver

ARG TAG_ARG
ARG BUILD_ARG
ENV TAG=$TAG_ARG
ENV BUILD=$BUILD_ARG

COPY scripts/docker_build_step2.sh /root/
COPY app/ $APP_DIR/
RUN bash /root/docker_build_step2.sh

EXPOSE 8000
CMD ["/app/ops/web_launch.sh"]
