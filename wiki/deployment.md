# Deployment

DataMade hosts a [staging version](https://lametro.datamade.us/) and [production version](https://boardagendas.metro.net/) of Metro Councilmatic. 

Both sites reside on the [`metro-councilmatic` server](https://github.com/datamade/server-metro-councilmatic), an EC2 instance spun up in late 2018, after [the original Councilmatic server ran out of diskspace](https://github.com/datamade/devops/issues/55). Metro developers should be able to shell into this server, e.g., [for executing management commands](commands.md). If you cannot, then talk to your friendly DataMade devops team.

### Patterns and practices

Metro deployments follow a typical DataMade pattern: merging or pushing to master deploys to the staging site, and pushing a tag deploys to the production site. Metro Councilmatic also uses the "classic" style of DataMade deployment - or, conversely, Metro does not follow the contempary ["zero downtime" deployment pattern](https://github.com/datamade/deploy-a-site/blob/master/Zero-Downtime-Deployment.md). As a result, the Metro site raises a 500 error for a couple minutes, during the course of a codedeploy lifetime.

So, when can you trigger a deployment to production? DataMade *does not* need to communicate to the folks at Metro the exact timing of deployments. However, we do take a couple precautions:

1. Do not deploy during meetings, since we do not want the site to go down for a couple minutes, when users need access to event info.
2. Do not deploy on support Fridays, since we do not want the site behave unexpectedly, when Metro admin adds data on Friday night.

These practices have exceptions, of course, particularly, if Metro needs an urgent bug fix.

### Solr

Link to the README. Plus, other information?
