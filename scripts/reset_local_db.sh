#!/bin/sh

export PGUSER=postgres
export PGHOST=localhost
export PGPASSWORD=uptime
export PGPORT=15432

psql -d uptime -c 'DROP SCHEMA public CASCADE;CREATE SCHEMA public;'

make migrate
