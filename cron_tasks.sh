#! /bin/bash

cd /home/datamade/lametro-staging
/home/datamade/.virtualenvs/lametro-staging/bin/python manage.py loaddata >> /tmp/lametro-loaddata.log 2>&1
/home/datamade/.virtualenvs/lametro-staging/bin/python manage.py update_index