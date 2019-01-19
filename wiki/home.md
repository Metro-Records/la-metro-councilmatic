# A developer's guide to the Metro galaxy

"I’m sorry, but if you can’t be bothered to take an interest in local affairs, that’s your own lookout. Energize the demolition beams."

## Overview

[charts] [summary with words]


## Debugging data smells

Many issues can arise in the Metro galaxy, from the shallowest part of the frontend to the deepest end of the backend. Tackling data inaccuracies requires a strategic approach. This guide traces an easeful, step-by-step process for efficient debugging. 

DON'T PANIC. 

### Identifying the point of failure

[point to the charts in the overview that describe the data pipeline]

Data travels along a complicated path to arrive in Metro Councilmatic. Breakdown in the data pipeline can happen at four different points. 

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

It does not. The scrapers likely have a bug. Tracking down the exact nature of the bug may require some effort: fortunately, the scraper logs provide a good starting point. Shell into the server (`ssh ubuntu@ocd.datamade.us`), and tail the metro log (e.g. `tail -100 /tmp/lametro.log`). Hopefully, the log offers some clues. An OperationalError indicates that something went awry with the database (e.g., not enough diskspace), and a ScraperError indicates a particular issue with the one of the scraper repos.

If the scraper seems to be running without error, then the bug may be harder to find. A good first question: what are the most recent changes in the scraper codebase? could this have caused unusual behavior?

**Step 5. Look at Councilmatic database.** Shell inside the `metro-councilmatic` server (`ssh ubuntu@lametro.datamade.us`). Query the database, and look for data inaccuracies. You can do this via postgres or the Django shell: it's depends on the nature of the data problem, and your personal preferences. Is the data in the database?

It is! Great, move on to the next step.

It is not. The `import_data` command did not behave as expected. [more here]

**Step 6. Investigate the display logic.** [more here]


### Recurring problems

No mechanism for dealing with deleted source data: For example, sometimes metro staff has not edited an event, but deleted an event and created a new one. We do not have reliable way to tell when an items has been deleted from a downstream system so this creates duplicate events.


"last updated" flags not behaving as the scrapers expect: Problems in the data not appearing in the API. In addition to the API not containing every element, the "last updated" flags are not always updated when an item is updated. We have high freqency scrapers that try to only captures recently changed events, and then a nightly scraper that scrapes everything. 


## Deployment

[describe where things are deployed; what they are called]

### Practices

Do not deploy during meetings or on Friday.

### Solr

Link to the README. Plus, other information?



