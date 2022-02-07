import json


class RequestNotAuthenticated(Exception):

    def __init__(self):
        self.message = 'Request missing authentication'
        self.status_code = 401

class AuthenticationFailed(Exception):

    def __init__(self):
        self.message = 'Provided authentication is invalid'
        self.status_code = 403

class ResponseNotSerializable(Exception):

    def __init__(self, response):
        self.message = 'Response content could not be serialized to JSON'
        self.status_code = response.status_code
        self.reason = response.reason
