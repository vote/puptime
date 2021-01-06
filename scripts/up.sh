#!/bin/bash

trap "docker-compose down" EXIT

docker-compose up --build -d
docker-compose logs -f -t
