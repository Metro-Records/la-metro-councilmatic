import json


class UploadError(Exception):
    """Google Drive returned an error message when given a file to upload."""

    def __init__(self, response):
        self.response = json.loads(response)
        self.message = self.response['message']
        self.code = self.response['code']

    def __str__(self):
        return f'[Error {self.code}] {self.message}'
