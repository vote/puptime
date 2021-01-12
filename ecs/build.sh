#!/bin/bash

set -eu

cd "$(dirname "$0")"

# the container assumes the uid is 1000; mangle permissions to behave
# if we're not.
TARGETS="../scripts/remote_run.sh ./template/include/*.libsonnet ./template/*.jsonnet */*/*.json"
TARGETDIRS="generated/*"
chmod 777 $TARGETS $TARGETDIRS

cat <<"EOF" | docker run --rm -i --entrypoint bash -v $PWD/..:/app -w /app/ecs bitnami/jsonnet:latest
jsonnetfmt -i ./template/*.jsonnet
jsonnetfmt -i ./template/include/*.libsonnet


jsonnet ./template/service_web.jsonnet --ext-str env=dev > ./generated/dev/service_web.task.json
jsonnet ./template/service_beat.jsonnet --ext-str env=dev > ./generated/dev/service_beat.task.json
jsonnet ./template/service_worker.jsonnet --ext-str env=dev > ./generated/dev/service_worker.task.json

jsonnet ./template/service_web.jsonnet --ext-str env=staging > ./generated/staging/service_web.task.json
jsonnet ./template/service_beat.jsonnet --ext-str env=staging > ./generated/staging/service_beat.task.json
jsonnet ./template/service_worker.jsonnet --ext-str env=staging > ./generated/staging/service_worker.task.json

jsonnet ./template/service_web.jsonnet --ext-str env=prod > ./generated/prod/service_web.task.json
jsonnet ./template/service_beat.jsonnet --ext-str env=prod > ./generated/prod/service_beat.task.json
jsonnet ./template/service_worker.jsonnet --ext-str env=prod > ./generated/prod/service_worker.task.json

jsonnet -S ./template/remote_run.jsonnet --ext-str env=prod > ../scripts/remote_run.sh
EOF

chmod 644 $TARGETS
chmod 755 $TARGETDIRS
