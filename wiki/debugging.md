# Debugging data issues

DON'T PANIC. 

Many issues can arise in the Metro galaxy, from the shallowest part of the frontend to the deepest end of the backend. Tackling data inaccuracies requires a strategic approach. This guide traces an easeful, step-by-step process for efficient debugging. 

If the bug-in-question feels like a familiar one, then read below about [recurring problems](#recurring-problems).

## Identifying the point of failure

[point to the charts in the overview that describe the data pipeline]

Data travels along a complicated path to arrive in Metro Councilmatic. A disruption in the data pipeline can happen at four different points. 

1. Legistar - the Legistar API or web interface displays inaccuracies, likely because Metro staff did not enter correct data 
2. OpenCivicData API - the DataMade scrapers did not properly port data to the API 
3. Metro Postgresql database – `import_data` did not properly port data to the Metro database (N.B., historically, the Councilmatic import_data command has been a source of myriad bugs.) 
4. the front end - the site display logic does not correctly show the data 

Fixing a bug begins with identifying at which point the pipeline failed. The following steps outline how to do this.

### Step 1. Find the `ocd_id` of the Bill (known as a "Board Report" in Metro), Event, Person, or Committee with the data issues. 

Every detail page logs the `ocd_id` to the console (or in the source view). Let's walk through an example. Visit the page for the [November 2018 Finance, Budget and Audit Commitee meeting](https://boardagendas.metro.net/event/finance-budget-and-audit-committee-8bffd562963b/), and open the console. You should see its OCD ID.

![Open the Console](https://github.com/datamade/la-metro-councilmatic/tree/master/lametro/static/images/wiki/open_console.png)

### Step 2. Visit the OCD API.

Copy the OCD ID, and append it to `https://ocd.datamade.us/`. For example, the above referenced event lives at:

```
https://ocd.datamade.us/ocd-event/4b2ebe06-6e17-4602-846a-8bffd562963b
```

### Step 3. Find the source URLs.

The OCD API provides links to the Legistar API and web interface. For example, the above mentioned event has source urls listed like so: 

![Source URLs](https://github.com/datamade/la-metro-councilmatic/tree/master/lametro/static/images/wiki/source_url.png)

Events scrape the Spanish language source (i.e., "api (spa)"), as well. In initial debugging, focus on the "api" and "web" sources – by visiting these links and checking that the data in Legistar appears as expected. Does it?

It does! Great, move onto the next step.

It does not. Even better – contact Metro staff, and let them know that the data discrepancy occurs in Legistar. STOP HERE.

### Step 4. Go back to the OCD API. 

Does the data appear as expected in the OCD API (e.g., https://ocd.datamade.us/ocd-event/4b2ebe06-6e17-4602-846a-8bffd562963b)?

It does! Great move onto the next step.

It does not. The scrapers likely have a bug. Tracking down the exact nature of the bug may require some effort: fortunately, the scraper logs provide a good starting point. Shell into the server, and tail the metro log: 

```bash
ssh ubuntu@ocd.datamade.us

tail -100 /tmp/lametro.log
```

Hopefully, the log offers some clues. An OperationalError indicates that something went awry with the database (e.g., not enough diskspace), and a ScraperError indicates a particular issue with the one of the scraper repos.

If the scraper seems to be running without error, then the bug may be harder to find. A good first question: what are the most recent changes in the scraper codebase? could this have caused unusual behavior? 

The scrapers work through the cooperation of several repos, and the bug fix may require investigating one or more of these repos. [`datamade/scrapers-us-municipal/tree/master/lametro`](https://github.com/datamade/scrapers-us-municipal/tree/master/lametro) contains Metro-specific code for the Bill, Event, and People scrapers. The Metro scrapers inherit from the LegistarScraper and LegistarAPIScraper defined in [`opencivicdata/python-legistar-scraper/tree/master/legistar`](https://github.com/opencivicdata/python-legistar-scraper/tree/master/legistar). All scrapers depend on [the Pupa framework](https://github.com/opencivicdata/pupa) for scraping and importing data using the OCD standard. Most likely, the bug resides in the Metro or python-legistar scrapers, but in excpetional cases, the bug may originate in Pupa.

Finally, you might consider the health of the OCD API hosted by DataMade. [`api.opencivicdata.org`](https://github.com/datamade/api.opencivicdata.org) is a Django project that makes the scraped data available online. It's highly unlikely that the bug lives here, unless the repo or one of its dependencies presents recent, impactful changes. 

[Visit the Metro galaxy overview](overview.md) for detailed charts and descriptions of this network of repos. 

If you need to manually trigger a scrape, then read about the process in the [Commands to know](commands.md) section.

### Step 5. Look at the Councilmatic database.

Shell inside the `metro-councilmatic` server (`ssh ubuntu@lametro.datamade.us`). Query the database, and look for data inaccuracies. You can do this via postgres (database: `lametro`) or the Django shell: it's depends on the nature of the data problem, and your personal preferences. Is the data in the database?

It is! Great, move on to the next step.

It is not. The `import_data` command did not behave as expected. Tail the import logs, and look for clues. A common import error is the IntegrityError, which may alert you to missing or duplicate data: read the error carefully, and investigate the `ocd_id` that raised the error. 

```bash
tail -100 /var/log/councilmatic/lametro-importdata.log
```  

As with the scraper, if the import seems to be running without error, then the bug may be harder to find. A good first question: what are the most recent changes in the `django-councilmatic` codebase (the import script, but also the data modeling)? could this have caused unusual behavior?

If you need to manually trigger an import, then read about the process in the [Commands to know](commands.md) section.

### Step 6. Investigate the display logic.

You successfully confirmed that the data landed, without failure, in the Metro Councilmatic database! The bug resides somewhere in `la-metro-councilmatic` or the parent app, `django-councilmatic`. You can work through this by, first, examining the output of the view code, and then, inspecting how the templates deal with the data. Again, be sure to ask: what are the most recent changes, and could they have affected the health of the code?

## Recurring problems

Currently, the scrapers and Councilmatic do not have a mechanism for dealing with deleted source data. Metro staff sometimes creates data in error and deletes it from Legistar, but not before the scrapers scrape it: as a result, duplicate data appears in Councilmatic. Follow [this Gist](https://gist.github.com/reginafcompton/2cb4d690c0253a22305929a334753959) to learn about how to safely delete data from the OCD API and Councilmatic.

The "last updated" flags do not consistently behave as the scrapers expect, i.e., Metro staff change data in Legistar, but the "last updated" timestamp(s) do not change. This ongoing problem has been the source of [many](https://github.com/datamade/la-metro-councilmatic/issues/328), [many](https://github.com/opencivicdata/scrapers-us-municipal/issues/239) [issues](https://github.com/opencivicdata/scrapers-us-municipal/issues/256). In part, we mitigated this problem by increasing the scrape frequency for all events and all bills, on Friday, when Metro adds new data to the Legistar system. 
