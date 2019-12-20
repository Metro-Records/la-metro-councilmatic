#!/bin/bash -x
echo "Running release.sh"

echo "Migrating database"
python manage.py migrate --noinput
python manage.py import_shapes data/boundary.geojson

if [ "`psql ${DATABASE_URL} -tAX -c "SELECT COUNT(*) FROM opencivicdata_division"`" -eq "0" ]; then
    echo "Initializing pupa divisions"
    pupa dbinit us
fi

echo "Release finished"
