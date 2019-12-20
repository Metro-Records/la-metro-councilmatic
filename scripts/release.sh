#!/bin/bash -x
export HEROKU_DEBUG=1

python manage.py migrate --noinput
python manage.py collectstatic --noinput
