#!/bin/bash -e

trap "docker-compose stop" EXIT

docker-compose up --build -d
docker-compose logs -f -t --tail=100
