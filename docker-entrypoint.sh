#!/bin/sh
set -e

if [ "$DJANGO_MANAGEPY_MIGRATE" = 'on' ]; then
    python manage.py migrate --noinput
    python manage.py import_shapes data/final/boundary.geojson
fi

exec "$@"
