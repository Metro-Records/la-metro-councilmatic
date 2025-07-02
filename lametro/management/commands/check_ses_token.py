import requests
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

from smartlogic.client import SmartLogic


class Command(BaseCommand):
    """
    Checks the expiration date on the currently used SES api key.
    If we're two weeks away from the expiration or less, make a new key,
    and assign it to the appropriate config variable on the production, staging,
    and wagtail Heroku app environments.

    If the environment that is running this command has `DJANGO_DEBUG` set to `True`,
    then don't make a new api key. Instead, take the existing key, and assign it
    to a test variable set up on the wagtail app. The only environment that
    has that debug var set to `False` should be production.
    """

    help = (
        "Check SES api key expiration date. "
        + "Make a new one and swap it out if it's less than two weeks away."
    )

    def handle(self, *args, **kwargs):
        smartlogic = SmartLogic(settings.SMART_LOGIC_KEY)
        smartlogic._authorization = "Bearer {}".format(
            smartlogic.token()["access_token"]
        )
        api_key = smartlogic.get_api_key_details()
        expiration_dt = datetime.strptime(api_key["expiryDate"], "%Y-%m-%dT%H:%M:%SZ")
        two_weeks_before_exp = expiration_dt - timedelta(weeks=2)
        now = datetime.now()

        if now >= two_weeks_before_exp:
            # Update heroku environments with new key
            if settings.DEBUG:
                environments = ["wagtail"]
                new_key = api_key
                data = {
                    "TEST_VAR": f'test_dt: {now}, key: {new_key["apikey"]}',
                }
            else:
                environments = ["prod", "staging", "wagtail"]
                new_key = smartlogic.refresh_api_key()
                data = {
                    "SMART_LOGIC_KEY": new_key["apikey"],
                }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/vnd.heroku+json; version=3",
                "Authorization": f"Bearer {settings.HEROKU_KEY}",
            }

            for app in environments:
                url = f"https://api.heroku.com/apps/la-metro-councilmatic-{app}/config-vars"
                requests.patch(url, headers=headers, data=json.dumps(data))

            self.stdout.write("~~ Config vars updated! ~~")
        else:
            self.stdout.write(f"Key does not expire until {expiration_dt}")
