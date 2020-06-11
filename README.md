# Metro Board Reports

[Metro Board Reports](https://boardagendas.metro.net/) helps the Los Angeles community understand the activities of the Los Angeles County Metropolitan Transportation Authority (Metro) – a government agency that consists of several Board Members, who set policy, coordinate, plan, fund, build, and operate transit services and transportation programs throughout LA County.

The Metro Board Reports site monitors all things related to the Metro Board of Directors:

* the board reports introduced and passed
* its various committees and the meetings they hold
* the board members themselves

This site ultimately encourages greater public dialogue and increased awareness about transportation issues in LA County.

Metro Board Reports is a member of the [Councilmatic family](https://www.councilmatic.org/). Learn how to [build your own](https://github.com/datamade/councilmatic-starter-template) Councilmatic site!

## Setup

These days, we run apps in containers for local development. More on that [here](https://github.com/datamade/how-to/blob/master/docker/local-development.md). Prefer to run the app locally? See the [legacy setup instructions](https://github.com/datamade/la-metro-councilmatic/blob/b8bc14f6d90f1b05e24b5076b1bfcd5e0d37527a/README.md).

### Install OS level dependencies:

* [Docker](https://www.docker.com/get-started)

### Run the application

```bash
docker-compose up -d
```

Note that you can omit the `-d` flag to follow the application and service logs. If you prefer a quieter environment, you can view one log stream at a time with `docker-compose logs -f SERVICE_NAME`, where `SERVICE_NAME` is the name of one of the services defined in `docker-compose.yml`, e.g., `app`, `postgres`, etc.

When the command exits (`-d`) or your logs indicate that your app is up and running, visit http://localhost:8000 to visit your shiny, new local application!

### Load in the data

Every hour, DataMade scrapes the Legistar Web API and makes the results available on the Open Civic Data API, which hosts standardized data patterns about government organizations, people, legislation, and events. Metro Board Reports relies upon this data.

The django-councilmatic app comes with an `import_data` management command, which populates your database with content loaded from the OCD API. You can explore the nitty-gritty of this code [here](https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/import_data.py).

Run the `import_data` command, which may take a few minutes to an hour, depending on how much data you need to import. You can read more on how to limit the amount of data you import [in the wiki](https://github.com/datamade/la-metro-councilmatic/wiki/Commands-to-know#importing-data-to-councilmatic).

```bash
# Run the command in the background (-d) inside an application container.
# Remove the container when the command exits (--rm).
docker-compose run --rm -d app python manage.py import_data
```

For long-running data imports, you can view the logs like:

```bash
docker ps  # Look for the container named like la-metro-councilmatic_app_run_<SOME_ID>
docker-compose logs -f la-metro-councilmatic_app_run_<SOME_ID>
```

By default, the `import_data` command carefully looks at the OCD API; it is a smart management command. If you already have bills loaded, it will not look at everything on the API - it will look at the most recently updated bill in your database, see when that bill was last updated on the OCD API, and then look through everything on the API that was updated after that point.

If you'd like to load things that are older than what you currently have loaded, you can run the import_data management command with a `--delete` option, which removes everything from your database before loading.

Next, add your shiny new data to your search index with the `rebuild_index` command from Haystack.

```bash
docker-compose run --rm app python manage.py rebuild_index --batch-size=25
```

Once you've imported the data and added it to your index, create the cache, then you're all set!

```bash
docker-compose run --rm app python manage.py createcachetable
```

Head over to http://localhost:8000 to view the app.

## Making changes to the Solr schema

Did you make a change to the schema file that Solr uses to make its magic (`solr_configs/conf/schema.xml`)? Did you add a new field or adjust how solr indexes data? If so, you need to take a few steps – locally and on the server.

### Local development

First, remove your Solr container.

```
# remove your existing metro containers
docker-compose down

# build the containers anew
docker-compose up -d
```

Then, rebuild your index.

```
docker-compose run --rm app python manage.py rebuild_index --batch-size=25
```

### On the Server

The Dockerized versions of Solr on the server need your attention, too. Follow these steps.

1. Deploy the schema changes on the staging server.

2. Shell into the server, and go to the `lametro-staging` repo.
    ```bash
    ssh ubuntu@boardagendas.metro.net

    # Do not switch to the DataMade user!
    # Docker requires sudo priviliges
    cd /home/datamade/lametro-staging
    ```

3. Remove and rebuild the Solr container.
    ```bash
    # We need to stop the container before removing it!
    sudo docker stop lametro-staging-solr
    sudo docker rm lametro-staging-solr

    # -d is the daemon flag
    sudo docker-compose up -d solr-staging
    ```

4. Log in as the datamade user.
    ```bash
    sudo su - datamade
    ```

5. Rebuild the index for the staging server:
    ```bash
    workon lametro-staging
    python manage.py rebuild_index --batch-size=200
    ```

Did everything work as expected? Great - now onto the production site.

Make sure your changes are deployed to the production server (i.e. you've cut a release with your changes).

1. Look at the times cron tasks are run (specified in [`scripts/lametro-crontasks`](https://github.com/datamade/la-metro-councilmatic/blob/master/scripts/lametro-crontasks)), and plan to rebuild the index inbetween those times. Rebuilding the index will take a few minutes, so plan accordingly.

2. As above: shell into the server, go to the `lametro` repo, then remove and rebuild the Solr container.
    ```bash
    ssh ubuntu@boardagendas.metro.net
    cd /home/datamade/lametro

    sudo docker stop lametro-production-solr
    sudo docker rm lametro-production-solr

    sudo docker-compose up -d solr-production
    ```

3. Switch to the datamade user and rebuild the index.
    ```bash
    workon lametro
    python manage.py rebuild_index --batch-size=200
    ```

Nice! The production server should have the newly edited schema and freshly built index, ready to search, filter, and facet.

## A note on tests

LA Metro Councilmatic has a basic test suite. If you need to run it, simply run:

```bash
docker-compose -f docker-compose.yml -f tests/docker-compose.yml run --rm app
```

### Load testing

LA Metro Councilmatic uses [Locust](https://docs.locust.io/en/stable/) for load
testing. There is a starter script in `locustfile.py` that visits the homepage,
event listing, and an event detail page at random intervals between 60 and 90
seconds. This script was derived from user behavior in Google Analytics.
(If needed, request analytics access from Metro.)

You can run the load tests using the `locust` service in `docker-compose.locust.yml`:

```bash
docker-compose -f docker-compose.yml -f docker-compose.locust.yml run --service-ports --rm locust
```

This will start the Locust web server on http://localhost:8089. For more details,
see the [Locust documentation](https://docs.locust.io/en/stable/).

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/datamade/la-metro-councilmatic/issues

## Note on Patches/Pull Requests

* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2019 DataMade. Released under the [MIT License](https://github.com/datamade/la-metro-councilmatic/blob/master/LICENSE).
