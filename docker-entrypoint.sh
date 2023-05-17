#!/bin/sh
set -e

if [ "$DJANGO_MANAGEPY_MIGRATE" = 'on' ]; then
    python manage.py migrate --noinput
fi

if [ "$DJANGO_MANAGEPY_IMPORT_SHAPES" = 'on' ]; then
    python manage.py import_shapes data/final/boundary.geojson
fi

exec "$@"
