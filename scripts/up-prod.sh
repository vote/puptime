#!/bin/bash -e

trap "docker-compose -f docker-compose-prod.yaml stop" EXIT

docker-compose -f docker-compose-prod.yaml up -d
docker-compose -f docker-compose-prod.yaml logs -f -t --tail=100
