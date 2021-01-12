#!/bin/bash

trap "docker-compose stop" EXIT

docker-compose up --build -d
docker-compose logs -f -t
