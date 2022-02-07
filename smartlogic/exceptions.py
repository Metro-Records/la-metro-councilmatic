import json


class ResponseNotSerializable(Exception):

    def __init__(self, response):
        self.message = 'Response content could not be serialized to JSON'
        self.status_code = response.status_code
        self.reason = response.reason
