## Debugging data issues

Many issues can arise in the Metro galaxy, from the shallowest part of the frontend to the deepest end of the backend. Tackling data inaccuracies requires a strategic approach. This guide traces an easeful, step-by-step process for efficient debugging. 

DON'T PANIC. 

### Identifying the point of failure

[point to the charts in the overview that describe the data pipeline]

Data travels along a complicated path to arrive in Metro Councilmatic. A disruption in the data pipeline can happen at four different points. 

1. Legistar - the Legistar API or web interface did not provide accurate data 
2. OpenCivicData API - the DataMade scrapers did not properly port data to the API 
3. Metro Postgresql database – `import_data` did not properly port data to the Metro database (N.B., historically, the Councilmatic import_data command has been a source of myriad bugs.) 
4. the front end - the site display logic does not correctly show the data 

Fixing a bug begins with identifying at which point the pipeline failed. The following steps outline how to do this.

**Step 1. Find the `ocd_id` of the Bill, Event, Person, or Committee with the data issues.** Every detail page logs the `ocd_id` to the console (or in the source view). For example, open the console for this event: https://boardagendas.metro.net/event/regaular-board-meeting-db0f63e245f2/. You should see its id: ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2

**Step 2. Visit the OCD API.** Append the ID to `https://ocd.datamade.us/`. For example, the above referenced event lives at: https://ocd.datamade.us/ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2/

**Step 3. Find the source URLs.** The OCD API provides links to the Legistar API and web interface (look for the `source_url`). Open these, and check that the data in Legistar appears as expected.

It does! Great, move onto the next step.

It does not. Even better – contact Metro staff and let them know that the data discrepancy occurs in Legistar. Stop here.

**Step 4. Go back to the OCD API.** Does the data appear as expected in the OCD API  (e.g., https://ocd.datamade.us/ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2/)?

It does! Great move onto the next step.

It does not. The scrapers likely have a bug. Tracking down the exact nature of the bug may require some effort: fortunately, the scraper logs provide a good starting point. Shell into the server, and tail the metro log: 

```bash
ssh ubuntu@ocd.datamade.us

tail -100 /tmp/lametro.log
```

Hopefully, the log offers some clues. An OperationalError indicates that something went awry with the database (e.g., not enough diskspace), and a ScraperError indicates a particular issue with the one of the scraper repos.

If the scraper seems to be running without error, then the bug may be harder to find. A good first question: what are the most recent changes in the scraper codebase? could this have caused unusual behavior?

**Step 5. Look at the Councilmatic database.** Shell inside the `metro-councilmatic` server (`ssh ubuntu@lametro.datamade.us`). Query the database, and look for data inaccuracies. You can do this via postgres (database: `lametro`) or the Django shell: it's depends on the nature of the data problem, and your personal preferences. Is the data in the database?

It is! Great, move on to the next step.

It is not. The `import_data` command did not behave as expected. Tail the import logs, and look for clues. A common import error is the IntegrityError, which may alert you to missing or duplicate data: read the error carefully, and investigate the `ocd_id` that raised the error. 

```bash
tail -100 /var/log/councilmatic/lametro-importdata.log
```  

As with the scraper, if the import seems to be running without error, then the bug may be harder to find. A good first question: what are the most recent changes in the `django-councilmatic` codebase (the import script, but also the data modeling)? could this have caused unusual behavior?

**Step 6. Investigate the display logic.** You successfully confirmed that the data landed, without failure, in the Metro Councilmatic database! The bug resides somewhere in `la-metro-councilmatic` or the parent app, `django-councilmatic`. You can work through this by, first, examining the output of the view code, and then, inspecting how the templates deal with the data. Again, be sure to ask: what are the most recent changes, and could they have affected the health of the code?

### Recurring problems

Currently, the scrapers and Councilmatic do not have a mechanism for dealing with deleted source data. Metro staff sometimes creates data in error and deletes it from Legistar, but not before the scrapers scrape it: as a result, duplicate data appears in Councilmatic. Follow [this Gist](https://gist.github.com/reginafcompton/2cb4d690c0253a22305929a334753959) to learn about how to safely delete data from the OCD API and Councilmatic.

The "last updated" flags do not consistently behave as the scrapers expect, i.e., Metro staff change data in Legistar, but the "last updated" timestamp(s) do not change. This ongoing problem has been the source of [many](https://github.com/datamade/la-metro-councilmatic/issues/328), [many](https://github.com/opencivicdata/scrapers-us-municipal/issues/239) [issues](https://github.com/opencivicdata/scrapers-us-municipal/issues/256). In part, we mitigated this problem by increasing the scrape frequency for all events and all bills, on Friday, when Metro adds new data to the Legistar system. 
