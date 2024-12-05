#!/bin/bash
if [ -n "${PRODUCTION}" ] || [ -n "${STAGING}" ]; then
    set -euo pipefail

    python manage.py migrate --noinput
    python manage.py createcachetable
    python manage.py import_shapes data/final/boundary.geojson
    python manage.py clear_cache

    if [ `psql ${DATABASE_URL} -tAX -c "SELECT COUNT(*) FROM wagtailcore_page"` -eq "1" ]; then
       python manage.py load_content
    fi

else
    echo "PRODUCTION or STAGING is not set, skipping setup management commands"
fi
