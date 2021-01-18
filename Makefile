
# Running too many tests in parallel exhausts shared memory on some
# machines (recent Ubuntu and Fedora in my case).
MAXPROC ?= 16

up:
	scripts/up.sh

build:
	docker-compose build

makemigrations:
	docker-compose exec server python manage.py makemigrations

migrate:
	docker-compose exec server python manage.py migrate

createsuperuser:
	docker-compose exec server python manage.py createsuperuser

shell:
	docker-compose exec server /bin/bash

testpy:
	docker-compose exec server bash -c "TEST=1 pytest -n `scripts/nproc-max ${MAXPROC}` /app/"

mypy:
	docker-compose exec server mypy /app/

test:
	docker-compose exec server bash -c "TEST=1 pytest -n `scripts/nproc-max ${MAXPROC}` /app/ && mypy /app/"

lint:
	docker-compose exec server bash -c "autoflake \
		--remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports --in-place --recursive --exclude /*/migrations/* /app/ && \
		isort -m 3 -tc -w 88 --skip migrations /app/ && \
		black --exclude /*/migrations/* /app/"

make psql:
	PGPASSWORD=uptime psql uptime -h localhost -p 15432 -U postgres

shellprod:
	ENVIRONMENT=prod bash scripts/remote_run.sh "${TAG}" "${CMD}"

shellstaging:
	ENVIRONMENT=staging bash scripts/remote_run.sh "${TAG}" "${CMD}"

shelldev:
	ENVIRONMENT=dev DOCKER_REPO_NAME=uptimedev bash scripts/remote_run.sh "${TAG}" "${CMD}"

resetlocaldb:
	scripts/reset_local_db.sh
