# Commands to know

The LA metro galaxy comes with several CLI commands and their various options. This section identifies some of the most significant commands, how to use them, and where to execute them. 

## Scraping data from Legistar

Running the scrapers can be simple or fairly involved, given the number of options available. You can run full scrapes or "windowed" scrapes, you can run scrapes at faster or slower rates, or you can run scrapes for all data or just bills, events, or people. 

Note! The Metro scrapers on the server run at different intervals, depending on the day: roughly, the scrapers run a full scrape every night, scrape recently updated events and bills four times per hour Saturday through Thursday, and scrape all bills and events twice per hour on Fridays. [The crontask file includes the details.](https://github.com/datamade/scrapers-us-municipal/blob/master/scripts/scrapers-us-municipal-crontask#L12) 

If you need to manually intervene, then consider the below commands. (And as noted above, depending on the volume of the scrape, e.g., a scrape for all bills, you should consider turning off the crons.)

First, shell into the server.

```bash
# shell into the server
ssh ubuntu@ocd.datamade.us

# visit the scrapers directory, and launch the correct virtual environment
sudo su - datamade
cd scrapers-us-municipal
workon opencivicdata
```
Then, run the appropriate command.

```bash
# update all recently updated data
pupa update lametro

# update all recently updated data, but used cached pages
pupa update lametro --fastmode

# update all recently updated data, and move as quickly as possible (but do not use cache)
pupa update lametro --rpm=0 
```

```bash
# update bills from last 28 days
# https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/bills.py#L97
pupa update lametro bills

# update all bills
pupa update lametro bills window=0

# update bills from the last 7 days, using cached pages
pupa update lametro bills window=7 --fastmode
```

```bash
# update all events
# https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/events.py#L139
pupa update lametro events

# updated events from the last 7 days
pupa update lametro events window=7
```

```bash
# update all people
# the people scraper does not have a "window" argument, but instead determines which people to update by looking at those visible on the web interface
pupa update lametro people
```

## Importing data to Councilmatic

`django-councilmatic` comes with a lengthy, sometimes abstruse management command: `import_data`. The [LA Metro Councilmatic README offers some details on it](https://github.com/datamade/la-metro-councilmatic#import-data), and anyone who has the app running locally already knows something about `import_data`. 

Note! On the server, [the cron for the production site](https://github.com/datamade/la-metro-councilmatic/blob/master/scripts/lametro-crontasks) executes this command four times per hour. However, sometimes, you may need to kick off a manual import on the server to assist with debugging ventures. Depending on the volume of the import (e.g., an import for all data), you should consider turning off the crons or executing the command during the 15-minute window between cron processes.

```bash
# shell into the server
ssh ubuntu@lametro.datamade.us

# visit the production directory, and launch the correct virtual environment
sudo su - datamade
cd lametro
workon lametro

# run the command!
python manage.py import_data
```

The command, by default, considers only the most recently updated data. However, you can tell `import_data` to consider bills, people, organizations, and events with less recent `updated_at` timestamps. Why? The Councilmatic database may be missing past data (e.g., because a scraped failed without notice, several months ago). 

```bash
# run the command for many months ago
python manage.py import_data --update_since='2018-10-01'

# run the command, and update all data
python manage.py import_data --update_since='1900-01-01'
```

## Other commands

Did you manually run `import_data`? If so, you need to execute a few additional commands that aid in preparing the data for Councilmatic.

```bash
# a management command in django-councilmatic that refreshes the S3 Bucket document cache
# https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/refresh_pic.py
python manage.py refresh_pic
```

```bash 
# a management command that sends requests to the `metro-pdf-merger` with data about which reports to merge
# documented in the `metro-pdf-merger` README: https://github.com/datamade/metro-pdf-merger#get-started
python manage.py compile_pdfs

python manage.py compile_pdfs --all_documents
```

```bash
# a management command django-councilmatic that converts bill attachment into plain text (to enables searching for bills via attachments)
# https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/convert_attachment_text.py
python manage.py convert_attachment_text

# update all documents
python manage.py convert_attachment_text --update_all
```

```bash
# a Haystack command for updating or rebuilding the Solr index
# ideally, rebuild should be run with a small batch-size to avoid memory consumption issues
python manage.py rebuild_index --batch-size=200

# update can be run with an age argument, which instructs Solr to consider bills updated so many hours ago
python manage.py update_index --age=2
```

