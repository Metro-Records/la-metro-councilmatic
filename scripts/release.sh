#!/bin/bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py createcachetable
python manage.py import_shapes data/final/boundary.geojson
