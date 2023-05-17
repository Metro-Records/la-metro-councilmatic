from django.conf import settings

try:
    assert settings.SMART_LOGIC_ENVIRONMENT
except AssertionError:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "Please provide a value for SMART_LOGIC_ENVIRONMENT in settings.py"
    )

import json

import requests
from requests.exceptions import HTTPError, ConnectTimeout

from smartlogic.exceptions import (
    RequestFailed,
    RequestNotAuthenticated,
    AuthenticationFailed,
    ResponseNotSerializable,
)


class SmartLogic(object):
    BASE_URL = "https://cloud.smartlogic.com"
    SERVICE_URL = f"/svc/{settings.SMART_LOGIC_ENVIRONMENT}/ses/CombinedModel"

    def __init__(self, api_key, authorization=None):
        self.api_key = api_key
        self._authorization = authorization

    @property
    def auth_headers(self):
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._authorization,
        }

    def endpoint(self, method, route, **requests_kwargs):
        # Token requests are unauthenticated. Otherwise, short circuit if
        # authorization is not provided.
        if route != "/token" and not self._authorization:
            raise RequestNotAuthenticated

        url = f"{self.BASE_URL}{route}"

        try:
            response = getattr(requests, method)(url, timeout=5, **requests_kwargs)
        except (HTTPError, ConnectTimeout) as e:
            raise

        if response.status_code == 403:
            raise AuthenticationFailed

        elif response.status_code >= 400:
            raise RequestFailed(response=response)

        try:
            return response.json()
        except json.JSONDecodeError as e:
            response.status_code = (
                response.status_code if response.status_code != 200 else 500
            )
            response.reason = str(e)
            raise ResponseNotSerializable(response=response)

    def token(self):
        data = {"grant_type": "apikey", "key": self.api_key}
        return self.endpoint("post", "/token", data=data)

    def terms(self, params):
        return self.endpoint(
            "post",
            f"{self.SERVICE_URL}/terms.json",
            params=params,
            headers=self.auth_headers,
        )

    def concepts(self, term, params):
        return self.endpoint(
            "get",
            f"{self.SERVICE_URL}/concepts/{term}.json",
            params=params,
            headers=self.auth_headers,
        )
