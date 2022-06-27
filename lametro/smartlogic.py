import json

import requests
from requests.exceptions import HTTPError


class SmartLogic(object):
    BASE_URL = "https://cloud.smartlogic.com/"
    SERVICE_URL = "svc/0dcee7c7-1667-4164-81e5-c16e46f2f74c/ses/v1.2/CombinedModel/"

    def __init__(self, api_key):
        self.api_key = api_key
        self._token = self.token()["access_token"]

    @property
    def auth_headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer {}".format(self._token),
        }

    def endpoint(self, method, route, **kwargs):
        url = self.BASE_URL + route

        try:
            response = getattr(requests, method)(url, **kwargs)
        except HTTPError as e:
            raise

        try:
            return response.json()
        except json.JSONDecodeError:
            return response

    def token(self):
        data = {"grant_type": "apikey", "key": self.api_key}
        return self.endpoint("post", "token", data=data)

    def terms(self, params):
        return self.endpoint(
            "post",
            self.SERVICE_URL + "terms.json",
            params=params,
            headers=self.auth_headers,
        )
