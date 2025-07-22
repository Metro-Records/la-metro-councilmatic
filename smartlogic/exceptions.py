from requests.exceptions import JSONDecodeError


class RequestFailed(Exception):
    def __init__(self, response):
        try:
            self.message = f'Request failed for the following reason: {response.json()["error_description"]}'
        except JSONDecodeError:
            self.message = f"Request failed for the following reason: {response.status_code} - {response.reason}"
        self.status_code = response.status_code
        self.reason = response.reason
        super().__init__(self.message)


class RequestNotAuthenticated(Exception):
    def __init__(self):
        self.message = "Request missing authentication"
        self.status_code = 401
        super().__init__(self.message)


class AuthenticationFailed(Exception):
    def __init__(self):
        self.message = "Provided authentication is invalid"
        self.status_code = 403
        super().__init__(self.message)


class ResponseNotSerializable(Exception):
    def __init__(self, response):
        self.message = f"Response content could not be serialized to JSON for the following reason: {response.reason}"
        self.status_code = response.status_code
        self.reason = response.reason
        super().__init__(self.message)
