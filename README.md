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

## Setup Search

**Install Open JDK or update Java**

On Ubuntu:

``` bash
$ sudo apt-get update
$ sudo apt-get install openjdk-7-jre-headless
```

On OS X:

1. Download latest Java SE Development Kit from
[http://www.oracle.com/technetwork/java/javase/downloads/jdk10-downloads-4416644.html](http://www.oracle.com/technetwork/java/javase/downloads/jdk10-downloads-4416644.html)
2. Follow normal install procedure

**Download & setup Solr**

``` bash
wget http://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz
tar -xvf solr-4.10.4.tgz
sudo cp -R solr-4.10.4/example /opt/solr

# Copy schema.xml for this app to solr directory
sudo cp solr_scripts/schema.xml /opt/solr/solr/collection1/conf/schema.xml
```

**Run Solr**
```bash
# Next, start the java application that runs solr
# Do this in another terminal window & keep it running
# If you see error output, somethings wrong
cd /opt/solr
sudo java -jar start.jar
```

**Index the database**
```bash
# Do this in the la-metro-councilmatic directory:
python manage.py rebuild_index
```

**Regenerate Solr schema**

While developing, if you need to make changes to the fields that are getting
indexed or how they are getting indexed, you'll need to regenerate the
schema.xml file that Solr uses to make its magic. Here's how that works:

```
python manage.py build_solr_schema > solr_scripts/schema.xml
cp solr_scripts/schema.xml /opt/solr/solr/collection1/conf/schema.xml
```

In order for Solr to use the new schema file, you'll need to restart it.

**Using Solr for more than one Councilmatic on the same server**

If you intend to run more than one instance of Councilmatic on the same server,
you'll need to take a look at [this README](solr_scripts/README.md) to make sure you're
configuring things properly.

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
