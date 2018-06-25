# Data Flow and Debugging.

LA Metro has a complicated data flows.

1. First data is entered into the Legistar system by Metro staff
2. This data appears in Legistar site, and often, on the Legistar Web API. Not all information that appears on the Legistar website will appear in the API.
3. Our webscrapers are schedule to run at varying frequencies and pull information from the API and website and update the database that underlies ocd.datamade.us
4. The councilmatic application is regularly scheduled to import data from the ocd.datamade.us.
5. The councilmatic web application has logic that determines what elements to show on individual pages

If a client makes a change to their data, it can fail to be reflected on the councilmatic stage because of a problem at any one of these steps.

1. Problem of data entry: For example, sometimes metro staff has not edited an event, but deleted an event and created a new one. We do not have reliable way to tell when an items has been deleted from a downstream system so this creates duplicate events.
2. Problems in the data not appearing in the API. In addition to the API not containing every element, the "last updated" flags are not always updated when an item is updated. We have high freqency scrapers that try to only captures recently changed events, and then a nightly scraper that scrapes everything. 
3. Problems in our webscrapers. It sometimes happens there are bugs in our webscraper. Sometimes the server is full and the scrapers can't save the data. Other weird things happen
4. Problems in import_data: The Councilmatic import_data command has been a historic source of a lot of bugs, but has been fairly stable now. However, this code is complicated and introducing new features almost always introducdes new bugs
5. The LA Metro site can have pretty complicated display logic. It may have the data but not be showing in the right places.


# Debugging

The first step is to try to identify where things have broken down.

If you go to any detail page on the councilmatic site, you can open the console (or view the source) and get the ocd id for that item. For example, the ocd_id for https://boardagendas.metro.net/event/regaular-board-meeting-db0f63e245f2/ is ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2

That means our scraped data for this event is at https://ocd.datamade.us/ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2/

Once you get to the OCD page, you should check to make sure whether the right information is on that page.

If it is, the problem is in stages 4 or 5. Either there was a problem in getting the data into the councilmatic app, or there's a problem in our display logic

## The data is fine in OCD

If the data is fine in OCD, the next thing to check is to see if the data is fine in the councilmatic app. So, for these steps login into the councilmatic server.

If last updated field on the OCD page was within the past hour, I'll got ahead and rerun the `python manage.py import_data` command manually.

If that doesn't resolve the problem, I look at the data. I tend just use psql, but you can do this with `python manage.py shell` if you want to use the ORM. If the data looks okay, then I know I have a problem in my display logic.

If the data is not okay, then I know I have a bug in `import_data`.

## If the data is *not* fine in OCD

### If the data is OCD agrees with the Source Systems
If the data is not fine in OCD, the next step is to see whether we have the same data in OCD as in **both** source systems, both the legistar website and the web API.

On each OCD page, there are listings for the "sources" of the data. Those are the urls we need to check. So for example, https://ocd.datamade.us/ocd-event/d29f59be-6f5b-41ad-958f-db0f63e245f2/ has source of http://webapi.legistar.com/v1/metro/events/1331 and https://metro.legistar.com/MeetingDetail.aspx?ID=598589&GUID=FE629C30-8713-4E2A-816B-713ECAC10269&Options=info&Search= 

Is the information on thes pages the same as what appears on OCD? If so, then there was probably a problem with data entry and we are not talking about the same "event". The client may have not changed an entry but deleted and created a new one. This is even more likely if the source urls don't work or metro.legistar.com url that the client is referring to is different than the source url referenced on the OCD page.

If the client deleted an old entry and created a replacement, you will need to delete the entry from the ocd database.

### If the data is OCD does not agree with the source system.

The we have a problem in our scraping. The next thing to do is to verify that our scrapers are running. Login to ocd system, and
tail the relevant scraper log. They are located in the /tmp/ directory and the lametro scraper is called /tmp/lametro.log

You should be able to see the last time it ran and any problems it encountered.

If you are seeing OperationalErrors, there's something wrong with the database. Probably, the disk is full

If you are seeing ScraperError, then you are in luck and probably have a good clue as to where the problem is.

If the scraper is running fine, then you have a bug that's likely going to be harder to find.


