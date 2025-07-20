#!/bin/bash
# Wait for PostgreSQL to be ready

set -e

host="$1"
port="$2"
user="$3"
db="$4"
shift 4
cmd="$@"

until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -p "$port" -U "$user" -d "$db" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd