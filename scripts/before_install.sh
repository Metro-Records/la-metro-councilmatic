#!/bin/bash

set -euo pipefail

rm -Rf /home/datamade/la-metro-councilmatic
mkdir -p /home/datamade/la-metro-councilmatic

# Make the directory for the ETL logs
mkdir -p /var/log/councilmatic
chown -R datamade.www-data /var/log/councilmatic

if [ "$DEPLOYMENT_GROUP_NAME" == "staging" ]
then
    # Preserve uploaded PDFs
    if /home/datamade/lametro-staging/lametro/static/pdf/agenda-*.pdf
    then
      mv /home/datamade/lametro-staging/lametro/static/pdf/agenda-*.pdf /tmp
    fi

    rm -Rf /home/datamade/lametro-staging
    mkdir -p /home/datamade/lametro-staging
fi
if [ "$DEPLOYMENT_GROUP_NAME" == "production" ]
then
    # Preserve uploaded PDFs
    if /home/datamade/lametro/lametro/static/pdf/agenda-*.pdf
    then
      mv /home/datamade/lametro/lametro/static/pdf/agenda-*.pdf /tmp
    fi

    rm -Rf /home/datamade/lametro
    mkdir -p /home/datamade/lametro
fi

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy