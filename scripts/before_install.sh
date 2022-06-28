#!/bin/bash

set -euo pipefail

# Make directory for project
mkdir -p /home/datamade/la-metro-councilmatic

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy
