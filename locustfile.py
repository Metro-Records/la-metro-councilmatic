from locust import HttpUser, TaskSet, task, between


class UserBehavior(TaskSet):
    @task
    def index(self):
        self.client.get("/")

    @task
    def events(self):
        self.client.get("/events/")

    @task
    def event_detail(self):
        self.client.get("/event/regular-board-meeting-9db63964de28/")


class WebsiteUser(HttpUser):
    host = "https://lametro-app-upgrade.datamade.us"
    tasks = [UserBehavior]
    # Average time on page is 1:18
    wait_time = between(60, 90)
