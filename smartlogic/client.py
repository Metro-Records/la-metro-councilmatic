import json

import requests
from requests.exceptions import HTTPError


class SmartLogic(object):
    BASE_URL = "https://cloud.smartlogic.com/"
    SERVICE_URL = "svc/d3807554-347e-4091-90ea-f107a906aaff/ses/CombinedModel/"

    def __init__(self, api_key, authorization=None):
        self.api_key = api_key
        self._authorization = authorization if authorization \
            else 'Bearer {}'.format(self.token()['access_token'])

    @property
    def auth_headers(self):
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': self._authorization
        }

    def endpoint(self, method, route, **requests_kwargs):
        url = self.BASE_URL + route

        try:
            response = getattr(requests, method)(url, **requests_kwargs)
        except HTTPError as e:
            raise

        try:
            return response.json()
        except json.JSONDecodeError:
            return {'response': response.content.decode('utf-8')}

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

    def concepts(self, term, params):
        return self.endpoint(
           'get',
           self.SERVICE_URL + 'concepts/' + term + '.json',
           params=params,
           headers=self.auth_headers
        )