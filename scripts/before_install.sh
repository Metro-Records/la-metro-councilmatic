#!/bin/bash

set -euo pipefail

# Make directory for project
mkdir -p /home/datamade/lametro

source /home/datamade/lametro/configs/$DEPLOYMENT_GROUP_NAME-config.conf

# Preserve uploaded PDFs
mv /home/datamade/$APP_NAME/lametro/static/pdf/agenda-*.pdf /tmp

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy
