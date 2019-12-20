#!/bin/bash -x
echo "Running release.sh"

echo "Migrating database"
python manage.py migrate --noinput
python manage.py import_shapes data/boundary.geojson

echo "Release finished"
