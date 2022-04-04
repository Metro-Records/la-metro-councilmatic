import json


class UploadError(Exception):
    """Google Drive returned an error message when given a file to upload."""

    def __init__(self, response):
        self.response = json.loads(response)
        self.message = self.response['message']

    def __str__(self):
        return self.message


class DriveBuildError(Exception):
    """Couldn't connect to Google Drive"""

    def __init__(self, e):
        self.error = e

    def __str__(self):
        return self.error
