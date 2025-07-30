import requests
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

from smartlogic.client import SmartLogic
from lametro.exceptions import HerokuRequestError


class Command(BaseCommand):
    """
    Checks the expiration date on the current SES api token/key.
    If we're two weeks away from the expiration or less, and the `--update_token` flag
    is present, then make a new key and assign it to the appropriate config variable
    on Heroku. Use `--force_var_update` to replace the config vars on Heroku
    regardless of when the key expires.

    Omit the `--update_token` flag to prevent this command from making a new api key.
    Instead, this will take the existing key and assign it to a test variable
    set up on the staging app for development purposes.
    """

    help = (
        "Check SES api key expiration date. If specified, "
        + "make a new one and swap it out if it's less than two weeks away."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--update_token",
            action="store_true",
            help=(
                "Make a new token and assign its value to "
                + "the `SMART_LOGIC_KEY` config var in Heroku."
            ),
        )

        parser.add_argument(
            "--force_var_update",
            action="store_true",
            help=(
                "Force an update to Heroku config vars "
                + "regardless of whether the expiration date is near."
            ),
        )

    def handle(self, *args, **options):
        update_token = options.get("update_token")
        force_var_update = options.get("force_var_update")
        smartlogic = SmartLogic(settings.SMART_LOGIC_KEY)
        smartlogic._authorization = "Bearer {}".format(
            smartlogic.token()["access_token"]
        )
        api_key = smartlogic.get_api_key_details()
        expiration_dt = datetime.strptime(api_key["expiryDate"], "%Y-%m-%dT%H:%M:%SZ")
        two_weeks_before_exp = expiration_dt - timedelta(weeks=2)
        now = datetime.now()

        if now >= two_weeks_before_exp or force_var_update:
            # Ensure the heroku key is valid before making a new ses key
            if settings.HEROKU_KEY:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/vnd.heroku+json; version=3",
                    "Authorization": f"Bearer {settings.HEROKU_KEY}",
                }
                test_res = requests.get(
                    "https://api.heroku.com/apps/la-metro-councilmatic-staging",
                    headers=headers,
                )

                if test_res.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Heroku returned a {test_res.status_code} status code. "
                            + f"Error: {test_res.json()}"
                        )
                    )
                    return
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "HEROKU_KEY empty. "
                        + "Please supply an api key in order to update the config vars."
                    )
                )
                return

            # Prepare to update heroku config vars
            if update_token:
                # Make a brand new key for all environment(s)
                environments = ["wagtail", "staging", "prod"]
                new_key = smartlogic.refresh_api_key()
                data = {
                    "SMART_LOGIC_KEY": new_key["apikey"],
                }
            else:
                # This is the dev case. Do not make a new key,
                # and only update the test var in staging environment
                environments = ["staging"]
                data = {
                    "HEROKU_UPDATE_TEST_VAR": f'test_dt: {now}, key: {api_key["apikey"]}',
                }

            for app in environments:
                url = f"https://api.heroku.com/apps/la-metro-councilmatic-{app}/config-vars"
                res = requests.patch(url, headers=headers, data=json.dumps(data))
                if res.status_code != 200:
                    raise HerokuRequestError(response=res)

            self.stdout.write(
                f"~~ Config vars updated for: {', '.join(environments)} ~~"
            )
        else:
            # There is no need to update the token yet
            self.stdout.write(f"Key does not expire until {expiration_dt}")
