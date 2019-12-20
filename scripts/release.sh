#!/bin/bash -x
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Set ${TABLE} to the name of a table that you expect to have data in it.
if [ `psql ${DATABASE_URL} -tAX -c "SELECT COUNT(*) FROM opencivicdata_division"` -eq "0" ]; then
    pupa dbinit us
fi
