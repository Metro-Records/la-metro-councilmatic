import json
from requests.exceptions import JSONDecodeError


class UploadError(Exception):
    """Google Drive returned an error message when given a file to upload."""

    def __init__(self, response):
        self.response = json.loads(response)
        self.message = self.response["message"]
        self.code = self.response["code"]

    def __str__(self):
        return f"[Error {self.code}] {self.message}"


class HerokuRequestError(Exception):
    """Heroku returned an error when connecting through the api"""

    def __init__(self, response):
        try:
            self.message = (
                f'Request failed for the following reason: {response.json()["message"]}'
            )
        except (JSONDecodeError, KeyError):
            self.message = (
                "Request failed for the following reason: "
                + f"{response.status_code} - {response.reason}"
            )
        self.status_code = response.status_code
        self.reason = response.reason

        super().__init__(self.message)
