# Metro Board Reports

[Metro Board Reports](https://boardagendas.metro.net/) helps the Los Angeles community understand the activities of the Los Angeles County Metropolitan Transportation Authority (Metro) – a government agency that consists of several Board Members, who set policy, coordinate, plan, fund, build, and operate transit services and transportation programs throughout LA County.

The Metro Board Reports site monitors all things related to the Metro Board of Directors:

* the board reports introduced and passed
* its various committees and the meetings they hold
* the board members themselves

This site ultimately encourages greater public dialogue and increased awareness about transportation issues in LA County.

Metro Board Reports is a member of the [Councilmatic family](https://www.councilmatic.org/). Learn how to [build your own](https://github.com/datamade/councilmatic-starter-template) Councilmatic site!

## Setup

**Install OS level dependencies:**

* Python 3.4
* PostgreSQL 9.4 +

**Install app requirements**

We recommend using [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html) and [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/install.html) for working in a virtualized development environment. [Read how to set up virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

Once you have virtualenvwrapper set up, run the following in your terminal:

```bash
mkvirtualenv la-metro
git clone git@github.com:datamade/la-metro-councilmatic.git
cd la-metro-councilmatic
pip install -r requirements.txt
```

Afterwards, whenever you want to use this virtual environment, run `workon la-metro`.

**Special installation requirements**

Metro runs a custom script that converts board-report attachments into plaintext. The script uses `textract` for conversions. Mac users can [follow the instructions given by `textract`](http://textract.readthedocs.io/en/stable/installation.html#osx).

For Ubuntu users and on the server, the `textract` installation instructions require a little remediation. Follow these steps:

(1) [Install all the dependencies](http://textract.readthedocs.io/en/stable/installation.html#ubuntu-debian).

(2) `textract` fails when installing `pocketsphinx`. Happily, `textract` does not need this dependency for converting PDFs or word documents into plain text. [This issue offers a script that installs a "fake pocketsphinx"](https://github.com/deanmalmgren/textract/pull/178). Do as the issue instructs.

(3) You're ready! Inside your virtualenv execute: `pip install textract==1.6.1`.


**Create your settings file**

```bash
cp councilmatic/settings_deployment.py.example councilmatic/settings_deployment.py
```

Then edit `councilmatic/settings_deployment.py`:
- `USER` should be your username

**Setup your database**

Before we can run the website, we need to create a database.

```bash
createdb lametro
```

Then, run migrations:

```bash
python manage.py migrate
```

Create an admin user. Terminal will prompt you to provide a username, email, and password. This superuser has access to the Django admin backend.

```bash
python manage.py createsuperuser
```

## Import data

Every hour, DataMade scrapes the Legistar Web API and makes the results available on the Open Civic Data API, which hosts standardized data patterns about government organizations, people, legislation, and events. Metro Board Reports relies upon this data.

The django-councilmatic app comes with an `import_data` management command, which populates your database with content loaded from the OCD API. You can explore the nitty-gritty of this code [here](https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/import_data.py).

Run the `import_data` command, which may take a few minutes, depending on volume:

```bash
python manage.py import_data
```

By default, the import_data command carefully looks at the OCD API; it is a smart management command. If you already have bills loaded, it will not look at everything on the API - it will look at the most recently updated bill in your database, see when that bill was last updated on the OCD API, and then look through everything on the API that was updated after that point. If you'd like to load things that are older than what you currently have loaded, you can run the import_data management command with a `--delete` option, which removes everything from your database before loading.

The import_data command has some more nuance than the description above, for the different types of data it loads. If you have any questions, open up an issue and pester us to write better documentation.

Once you've imported the data, create the cache, then you're all set!

```bash
python manage.py createcachetable
```

## Run Metro Board Reports locally

Run the following in terminal:

``` bash
python manage.py runserver
```

Then, navigate to http://localhost:8000/.

## Solr Search

### Get setup

LA Metro containerizes Solr with Docker. Be sure you have [Docker on your local machine](https://www.docker.com/get-started), and then, follow these steps.

1. Peek inside the `docker-compose.yml` file. It has configurations for two solr containers: staging and production. Staging runs on port 8986, and production runs on port 8985. Use 8986 (lametro-staging) for local development. Specify it in `settings_deployment.py`.

```
# councilmatic/settings_deployment.py

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8986/solr/lametro-staging',
    },
}
```

2. Now, run docker! 

```
docker-compose up solr-staging
```

### Regenerate Solr schema

Did you make a change to the schema file that Solr uses to make its magic (`solr_configs/conf/schema.xml`)? Did you add a new field or adjust how solr indexes data? If so, you need to take a few steps – locally and on the server.

**Local development**

First, remove the solr container.  

```
# view all containers
docker ps -a

# remove the solr container
docker rm lametro-{{deployment}}-solr

# build the container anew
docker-compose up solr-{{deployment}}
```

Then, rebuild your index.

```
python manage.py rebuild_index
```

Finally, prepare for deployment: move your new schema to `solr_scripts`.

```
cp solr_configs/conf/schema.xml solr_scripts/schema.xml
```

**On the Sever**

The Dockerized versions of Solr on the server need your attention, too. Follow these steps.

1. Deploy the schema changes on the staging server. 
2. Shell into the server, go to the `lametro-staging` repo, and remove and rebuild the Solr container.

```
docker rm lametro-staging-solr
docker-compose up solr-staging
```

3. Rebuild the index for the staging server: `python manage.py rebuild_index`.

Did everything work as expected? Great - now onto the production site. 

1. Contact the folks at Metro and let them know the search funcitonality and data import will be down for a short period.
2. Turn off the crons (`lametro-crontasks`) - do this in a pull request.
3. Deploy the schema changes to the production server.
4. As above: shell into the server, go to the `lametro` repo, and remove and rebuild the Solr container.
5. Rebuild the index.
6. Turn on the crons - again, do this in a pull request!

Nice! The production server should have the newly edited schema and freshly built index, ready to search, filter, and facet. 

## A note on tests

LA Metro Councilmatic has a basic test suite. If you need to run it, simply run:

```bash
pytest
```

## Team

* Forest Gregg, DataMade - Open Civic Data (OCD) and Legistar scraping
* Eric van Zanten, DataMade - search and dev ops
* Regina Compton, DataMade - developer

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/datamade/nyc-councilmatic/issues

## Note on Patches/Pull Requests

* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2017 DataMade. Released under the [MIT License](https://github.com/datamade/nyc-councilmatic/blob/master/LICENSE).
