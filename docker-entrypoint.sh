#!/bin/sh
set -e

if [ "$DJANGO_MANAGEPY_MIGRATE" = 'on' ]; then
    python manage.py migrate --noinput
    python manage.py import_shapes data/boundary.geojson
fi

if [ "$DECRYPT_SECRETS" = 'on' ]; then
    blackbox_postdeploy
fi

exec "$@"
