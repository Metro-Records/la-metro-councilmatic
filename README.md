# Metro Board Reports

[Metro Board Reports](https://boardagendas.metro.net/) helps the Los Angeles community understand the activities of the Los Angeles County Metropolitan Transportation Authority (Metro) – a government agency that consists of several Board Members, who set policy, coordinate, plan, fund, build, and operate transit services and transportation programs throughout LA County.

The Metro Board Reports site monitors all things related to the Metro Board of Directors:

* the board reports introduced and passed
* its various committees and the meetings they hold
* the board members themselves

This site ultimately encourages greater public dialogue and increased awareness about transportation issues in LA County.

Metro Board Reports is a member of the [Councilmatic family](https://www.councilmatic.org/). Learn how to [build your own](https://github.com/datamade/councilmatic-starter-template) Councilmatic site!

## Setup

These days, we run apps in containers for local development. More on that [here](https://github.com/datamade/how-to/docker/local-development.md).

### Set-up pre-commit

We use the [pre-commit](https://pre-commit.com/) framework to use Git pre-commit hooks that keep our codebase clean.

To set up Pre-Commit, install the Python package on your local machine using

```bash
python -m pip install pre-commit
```

If you'd rather not install pre-commit globally, create and activate a [virtual environment](https://docs.python.org/3/library/venv.html) in this repo before running the above command.

Then, run

```bash
pre-commit install
```

to set up the git hooks.

Since hooks are run locally, you can modify which scripts are run before each commit by modifying `.pre-commit-config.yaml`.

### Get the Legistar API key

There should be an entry in the DataMade LastPass account called 'LA Metro - secrets.py.' Copy its contents into a file called `secrets.py` and place it in `lametro/`.

### Install OS level dependencies:

* [Docker](https://www.docker.com/get-started)

### Load in the data

The Metro app ingests updated data from the Legistar API several times an hour.

To import data into your local instance, copy DataMade's Legistar API token from
Bitwarden (search `LA Metro Legistar API Token`). Next, create a copy of the secrets
file and paste in the token:

```bash
cp lametro/secrets.py.example lametro/secrets.py
```

Then, simply run:

```bash
docker-compose run --rm scrapers
```

This may take a few minutes to an hour, depending on the volume of recent
updates.

### Run the application

First, create your own local env file:

```bash
cp .env.local.example .env.local
```

Next, bring up the app:

```bash
docker-compose up
```

When your logs indicate that your app is up and running, visit http://localhost:8001 to visit your shiny, new local application!

### Optional: Populate the search index

If you wish to use search in your local install, you need a SmartLogic API
key and the reCAPTCHA development keys. Initiated DataMade staff may retrieve values for
the `SMART_LOGIC_ENVIRONMENT` and `SMART_LOGIC_KEY` environment variables from Heroku:

```bash
heroku config:get SMART_LOGIC_ENVIRONMENT SMART_LOGIC_KEY -a la-metro-councilmatic-staging
```

Paste these values into your `.env.local` file.

Then, run the `refresh_guid` management command to grab the appropriate
classifications for topics in the database.

```bash
docker-compose exec app python manage.py refresh_guid
```

Finally, add data to your search index with the `update_index` command from
Haystack.


```bash
docker-compose run --rm app python manage.py update_index
```

When the command exits, your search index has been filled.

The reCAPTCHA keys will be found in a Bitwarden note titled "LA Metro Councilmatic - Dev recaptcha keys".
Similarly add both the public and private keys to your environment variables.

## Running arbitrary scrapes
Occasionally, after a while without running an event scrape, you may find that your local app is broken. If this happens, make sure you have events in your database that are scheduled for the future, as the app queries for upcoming events in order to render the landing page.

1. Make sure there are future events scheduled in Legistar. Go to the [LA Metro Legistar page](https://metro.legistar.com/Calendar.aspx) and open up the time filter for "All Years".

2. If you notice that there are future events in Legistar, run a small windowed event scrape:

```bash
docker-compose run --rm scrapers pupa update lametro events window=0.05 --rpm=0
```

This will bring in a few upcoming events, and your app will be able to load the landing page.

## Scraping specific bill
It's sometimes helpful to make sure you have a specific bill in your database for debugging. Here's how you can scrape a bill you need:

1. Go to the Legistar Web API at the following URL: http://webapi.legistar.com/v1/metro/matters/?$filter=MatterFile%20eq%20%27<bill_identifier>%27 and find the `<MatterId>` of the bill. The identifier should be in XXXX-XXXX format, and the `MatterId` is a 4 digit number.

2. Run the following command in your shell:
```bash
docker-compose run --rm scrapers pupa update lametro bills matter_ids=<bill_matter_id> --rpm=0
```

## Connecting to AWS S3 for development

If you want to use the S3 bucket, you’ll need the AWS S3 API keys. This can be found by running:
```bash
heroku config:get AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY -a la-metro-councilmatic-staging
```

Grab the values for the `AWS_ACCESS_KEY_ID` and the `AWS_SECRET_ACCESS_KEY` and add them to your `.env.local` file.

Now you should be able to start uploading some files!

## Review Apps
This repo is set up to deploy review apps on Heroku, and those pull from the staging database to match the experience of deploying as closely as possible! However, note that in order to prevent unapproved model changes from effecting the staging database, migrations are prevented from running on review apps. So those will still have to be reviewed locally.

### Review apps for Wagtail changes

1. Configure the S3 connection, as documented above.
2. Once a release phase successfully completes, provision an Essential 0 database for your review app.
3. Retrieve the URI from the Credentials tab.
4. Update the app's `DATABASE_URL` config value to the new URI.
5. On your local machine, run `DATABASE_URL=<YOUR URI HERE> make -e wagtail_db`. This will populate initial legislative data and import content from the version controlled fixture data.

## Adding a new board member

Hooray! A new member has been elected or appointed to the Board of Directors.
There are a few changes you need to make so they appear correctly on the site.

### Update the scraper

- Add the new member to the `VOTING_POSTS` object [in the Metro person scraper](https://github.com/opencivicdata/scrapers-us-municipal/). Once your PR is reviewed, merge your changes, pull them into [our scrapers fork](https://github.com/datamade/scrapers-us-municipal/), and [follow the steps to deploy your change](https://github.com/datamade/scrapers-us-municipal/#deploying-changes).
    - Example: https://github.com/opencivicdata/scrapers-us-municipal/pull/337
    - Tip: Once your scraper change is deployed. Run `docker-compose run --rm scrapers pupa import lametro people --rpm=0` to capture the change locally.
- After the revised person scrape runs, remove any board memberships for the
new member that were created without a post.
    ```python
    from lametro.models import Person
    Person.objects.get(family_name='<MEMBER LAST NAME>').memberships.filter(organization__name='Board of Directors', post__isnull=True).delete()
    ```

### Check your work

To confirm your changes worked, run the app locally and confirm the following:

- View [the Board of Directors](https://boardagendas.metro.net/board-members/)
listing and confirm the new member is listed with the correct post, e.g.,
`Los Angeles Country Board Supervisor, District 1`.
    - If you only see `Board Member`, the new member's post has not been added.
    Double check that you updated the `VOTING_POSTS` object in the person
    scraper (e.g., does the member's name as it appears in the API match the
    key you added?), that your changes to the scraper have been deployed, and
    that a person scrape has been run since the deployment.

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

## Review Apps

This repo is set up to deploy review apps on Heroku, and those pull from the staging database to match the experience of deploying as closely as possible! However, note that in order to prevent unapproved model changes from effecting the staging database, migrations are prevented from running on review apps. So those will still have to be reviewed locally.

## Updating the Documentation

To make changes to the documentation, [install Quarto](https://quarto.org/docs/get-started/).

Then, run the following in your terminal:

```bash
quarto preview docs
```

Make your changes to the `.qmd` files in the `docs/` directory. They will be automatically
reflected in your local version of the docs.

For more on authoring docs with Quarto, see [their Getting Started guide](https://quarto.org/docs/get-started/authoring/text-editor.html) and [documentation](https://quarto.org/docs/guide/).

The GitHub Pages site will rebuild automatically when your documentation changes are
merged into `main`.

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/datamade/la-metro-councilmatic/issues

## Note on Patches/Pull Requests

* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2023 DataMade. Released under the [MIT License](https://github.com/datamade/la-metro-councilmatic/blob/main/LICENSE).
