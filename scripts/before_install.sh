#!/bin/bash

# Make project directory if it doesn't exist. This is mainly to ensure that these scripts work on a bare server
mkdir -p /home/datamade/la-metro-councilmatic

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown datamade.datamade . && sudo -H -u datamade blackbox_postdeploy
