#!/bin/bash
set -euo pipefail

# Make sure the deployment group specific variables are available to this
# script.
source ${BASH_SOURCE%/*}/../configs/$DEPLOYMENT_GROUP_NAME-config.conf

# Set some useful variables
PROJECT_DIR="/home/datamade/$APP_NAME-$DEPLOYMENT_ID"

# Re-read supervisor config, and add new processes
supervisorctl reread
supervisorctl add $APP_NAME-$DEPLOYMENT_ID

# Check to see if our /pong/ endpoint responds with the correct deployment ID.
loop_counter=0
while true; do
    # check to see if the socket file that the gunicorn process that is running
    # the app has been created. If not, wait for a second.
    if [[ -e /tmp/$APP_NAME-${DEPLOYMENT_ID}.sock ]]; then

        # Pipe an HTTP request into the netcat tool (nc) and grep the response
        # for the deployment ID. If it's not there, wait for a second.
        running_app=`printf "GET /pong/ HTTP/1.1 \r\nHost: localhost \r\n\r\n" | nc -U /tmp/$APP_NAME-${DEPLOYMENT_ID}.sock | grep -e "$DEPLOYMENT_ID" -e 'Bad deployment*'`
        echo $running_app
        if [[ $running_app == $DEPLOYMENT_ID ]] ; then
            echo "App matching $DEPLOYMENT_ID started"
            break
        elif [[ $loop_counter -ge 20 ]]; then
            echo "Application matching deployment $DEPLOYMENT_ID has failed to start"
            exit 99
        else
            echo "Waiting for app $DEPLOYMENT_ID to start"
            sleep 1
        fi
    elif [[ $loop_counter -ge 20 ]]; then
        echo "Application matching deployment $DEPLOYMENT_ID has failed to start"
        exit 99
    else
        echo "Waiting for socket $APP_NAME-$DEPLOYMENT_ID.sock to be created"
        sleep 1
    fi
    loop_counter=$(expr $loop_counter + 1)
done

# If everything is OK, check the integrity of the nginx configuration and
# reload (or start for the first time) Nginx. Because of the pipefail setting
# at the beginning of this script, if any of the configuration files that Nginx
# knows about contain errors, this will cause this script to exit with a non-zero
# status and cause the deployment as a whole to fail.
echo "Reloading nginx"
nginx -t
service nginx reload || service nginx start


# It's safe to terminate the older version of the site
# by sending the TERM signal to old supervisor processes.
old_deployments=`(supervisorctl status | grep -v $DEPLOYMENT_ID | grep RUNNING | cut -d ' ' -f 1) || echo ''`
for deployment in $old_deployments; do
    echo "Signalling application process $deployment"
    supervisorctl signal TERM $deployment
done;

# Once the app has started, reboot the Solr container using the current app
# docker-compose.deployment.yml. Data should be persisted between containers,
# thanks to our volume use.
[ -n "$(docker ps -f NAME=solr-$DEPLOYMENT_GROUP_NAME -q)" ] && \
    (docker stop solr-$DEPLOYMENT_GROUP_NAME; docker rm solr-$DEPLOYMENT_GROUP_NAME)

cd $PROJECT_DIR
docker-compose -f docker-compose.deployment.yml up -d solr-$DEPLOYMENT_GROUP_NAME

# Cleanup all versions except the most recent 3. This uses the find command to
# search for directories within the home directory of the datamade user, sorts
# them by when they were created, then filters them down to only the directory
# names that are for our project and reduces them down to the top three in the
# list (which should be the most recent)

old_versions=`(find /home/datamade -maxdepth 1 -type d -printf '%TY-%Tm-%Td %TT %p\n' | sort -r | grep -Po "/home/datamade/$APP_NAME-d-[A-Z0-9]{9}" | tail -n +4) || echo ''`
for version in $old_versions; do
    echo "Removing $version"
    rm -rf $version
done;

# Cleanup virtualenvs except the most recent 3. This uses the same approach as
# above but for virtual environments rather than the code directories.
old_venvs=`(find /home/datamade/.virtualenvs -maxdepth 1 -type d -printf '%TY-%Tm-%Td %TT %p\n' | sort -r | grep -Po "/home/datamade/\.virtualenvs/$APP_NAME-d-[A-Z0-9]{9}" | tail -n +4) || echo ''`
for venv in $old_venvs; do
    echo "Removing $venv"
    rm -rf $venv
done;

# Remove old processes from supervisor. Search the output of the status command
# of Supervisor for those processes that have exited, are stopped or died on
# their own and look for the ones that are for our project. The processes that we
# sent the TERM signal to above should be amongst these.

old_procs=`(supervisorctl status | grep -P '(EXITED|STOPPED|FATAL)' | cut -d: -f 1) || echo ''`
for proc in $old_procs; do
    echo "Removing $proc"
    supervisorctl remove $proc
done;