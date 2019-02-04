# Commands to know

The LA metro galaxy comes with several CLI commands and their various options. This section identifies some of the most significant commands, how to use them, where to execute them, and [where to log the output](#logs). 

## Logs

The Metro data pipeline depends on crontasks, i.e., regularly scheduled processes that occur on the servers. We keep these under version control, and so, you can easily reference them: 

* [scrapers-us-municipal cron](https://github.com/datamade/scrapers-us-municipal/blob/master/scripts/scrapers-us-municipal-crontask)
* [Councilmatic cron](https://github.com/datamade/la-metro-councilmatic/blob/master/scripts/lametro-crontasks)

The crontasks log every scrape, import, cache refresh, document conversion, and Solr update. These logs help us maintain reliable records of our data pipeline – something particularly meaningful [when the pipeline fails](debugging.md). Manually executed commands should be recorded, too. Ideally, the command output should be preserved in the same log that the crontasks point to. 

```
# example
# 2>&1 silences command output and redirects it to the specified location
python manage.py import_data >> /var/log/councilmatic/lametro-importdata.log 2>&1
``` 

Notably, we do not place logs in the `/tmp` directory, because it gets wiped when the server reboots. This happens very, very rarely, but when it does, the logs carry great significance for debugging. 

## Scraping data from Legistar

Running the scrapers can be simple or fairly involved. You can run full scrapes or "windowed" scrapes; you can run scrapes at faster or slower rates; you can run scrapes for all data or just bills, events, or people (oh, my). 

**Note!** The Metro scrapers on the server run at different intervals, depending on the day. [The crontask file includes the details](https://github.com/datamade/scrapers-us-municipal/blob/master/scripts/scrapers-us-municipal-crontask#L12). (Learn how to decipher the specifics of crontasks with [the beloved crontab guru](https://crontab.guru/).) Roughly, the scrapers: 
* run a full scrape every night
* scrape recently updated events and bills, four times per hour, Saturday through Friday morning
* scrape all bills and events twice per hour on Friday evenings  

Sometimes, you may need to run a scrape on the server to assist with debugging ventures. If so, then consider the below commands. 

**Hold on!** What about the commands auto-executed via cronjobs? You do not want a cronjob to collide with a manual run of the scraper: such collisions can raise an IntegrityError or other database issues, which will necessitate redoing the scraper (...and placing your palm firmly on your forehead). A scrape may take longer than 15 minutes, e.g., a scrape for all bills: if so, you should consider turning off the crons, [via a pull request](https://github.com/datamade/scrapers-us-municipal/pull/20), before executing these commands on the server. However, scraping all bills from the last two days, for example, should be relatively fast. Leave the crons on for a scrape of this size.

All right. First, get situated on the server.

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
# scrape all recently updated data
pupa update lametro

# scrape all recently updated data, but used cached pages
# avoid fastmode for larger scrapes, since you risk scraping out-of-date data
# instead, use the `rpm` option (see below)
pupa update lametro --fastmode

# scrape all recently updated data, and move as quickly as possible (but do not use cache)
pupa update lametro --rpm=0 
```

```bash
# scrape bills updated in the last 28 days
# https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/bills.py#L97
pupa update lametro bills

# scrape all bills
pupa update lametro bills window=0

# scrape bills updated in the last 7 days, using cached pages
pupa update lametro bills window=7 --fastmode
```

```bash
# scrape all events
# https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/events.py#L139
pupa update lametro events

# scrape events updated in the last 7 days
pupa update lametro events window=7
```

```bash
# scrape all people
# the people scraper does not have a "window" argument
# but instead determines which people to update by looking at those visible on the web interface
pupa update lametro people
```

## Importing data to Councilmatic

`django-councilmatic` comes with a lengthy, sometimes abstruse management command: `import_data`. The [LA Metro Councilmatic README offers some details on it](https://github.com/datamade/la-metro-councilmatic#import-data), and anyone who has the app running locally already knows something about `import_data`. 

**Note!** On the server, [the cron for the production site](https://github.com/datamade/la-metro-councilmatic/blob/master/scripts/lametro-crontasks) executes this command four times per hour. You may need to manually intervene, however. As with the scraper, consider turning off the crons or executing the command during the 15-minute window between cron processes: usually the import runs quickly, so running the command between cronjobs often works best. 

```bash
# shell into the server
ssh ubuntu@lametro.datamade.us

# visit the production directory, and launch the correct virtual environment
sudo su - datamade
cd lametro
workon lametro

# run the command and log the results (if on the server)
python manage.py import_data >> /var/log/councilmatic/lametro-importdata.log 2>&1
```

The command, by default, considers only the most recently updated data. However, you can tell `import_data` to consider bills, people, organizations, and events with less recent `updated_at` timestamps. Why? The Councilmatic database may be missing past data (e.g., because the scraper failed without notice, several months ago). 

```bash
# import data updated on October 1, 2018 and after 
python manage.py import_data --update_since='2018-10-01'

# import all data
python manage.py import_data --update_since='1900-01-01'
```

## Other commands

Metro Councilmatic runs additional processes on the data, after it gets imported to the database. The commands below address the sundry data needs of the Metro system.

**Refresh the Property Image Cache.** Metro caches PDFs of board reports and event agendas. [This can raise issues.](https://github.com/datamade/la-metro-councilmatic/issues/347) The [`refresh_pic` management command](https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/refresh_pic.py) refreshes the document cache ([an S3 bucket connected to Metro Councilmatic via `property-image-cache`](https://github.com/datamade/property-image-cache)) by deleting potentially out-of-date versions of board reports and agendas. 

```bash
# run the command and log the results (if on the server)
python manage.py refresh_pic >> /var/log/councilmatic/lametro-refreshpic.log 2>&1
```

**Create PDF packets.** Metro Councilmatic has composite versions of the Event agendas (the event and all related board reports) and board reports (the report and its attachments). [A separate app assists in creating these PDF packets](https://github.com/datamade/metro-pdf-merger), and the [`compile_pdfs` command](https://github.com/datamade/la-metro-councilmatic/blob/master/lametro/management/commands/compile_pdfs.py) communicates with this app by telling it which packets to create.

```bash 
# run the command and log the results (if on the server)
# documented in the `metro-pdf-merger` README: https://github.com/datamade/metro-pdf-merger#get-started
python manage.py compile_pdfs >> /var/log/councilmatic/lametro-compilepdfs.log 2>&1

python manage.py compile_pdfs --all_documents
```

**Convert report attachments into plain text.** Metro Councilmatic allows users to query board reports via attachment text. The attachments must appear as plain text in the database: [`convert_attachment_text`](https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/convert_attachment_text.py) helps accomplish this.
```bash
# run the command and log the results (if on the server)
python manage.py convert_attachment_text >> /var/log/councilmatic/lametro-convertattachments.log 2>&1

# update all documents
python manage.py convert_attachment_text --update_all
```

**Rebuild or update the Solr search index.** Haystack comes with a utility command for rebuilding and updating the search index. [Learn more in the Haystack docs.](https://django-haystack.readthedocs.io/en/master/management_commands.html)

```bash
# ideally, rebuild should be run with a small batch-size to avoid memory consumption issues
# https://github.com/datamade/devops/issues/42
# run the command and log the results (if on the server)
python manage.py rebuild_index --batch-size=200 >> /var/log/councilmatic/lametro-updateindex.log 2>&1

# update can be run with an age argument, which instructs Solr to consider bills updated so many hours ago
python manage.py update_index --age=2

# update should be run in non-interactive mode, when logging the results
# `noinput` tells Haystack to skips the prompts
python manage.py update_index --noinput
```

**Are the Solr index and Councilmatic database in sync?** Sometimes, the Solr index falls behind the Councilmatic database. This issue arises for a number of reasons and, resultantly, [causes headaches](https://github.com/datamade/la-metro-councilmatic/issues/256). The [`data_integrity` script](https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/data_integrity.py) checks that the Councilmatic database has the same number of records as the Solr index. 

```
# run the command and log the results (if on the server)
python manage.py data_integrity >> /var/log/councilmatic/lametro-integrity.log 2>&1
```

Appropriately, `data_integrity` executes at the very end of the crontab, a (usually) happy conclusion to the marching progression of Metro commands.
