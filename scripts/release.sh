#!/bin/bash

if [ -n "${PRODUCTION}" ] || [ -n "${STAGING}" ]; then
    set -euo pipefail

    python manage.py migrate --noinput
    python manage.py createcachetable
    python manage.py import_shapes data/final/boundary.geojson
    python manage.py clear_cache

else
    echo "PRODUCTION or STAGING is not set, skipping setup management commands"
fi
