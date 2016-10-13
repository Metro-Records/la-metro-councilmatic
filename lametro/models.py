from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Event, Post
from datetime import datetime
import pytz

app_timezone = pytz.timezone(settings.TIME_ZONE)

class LAMetroBill(Bill):

	class Meta:
		proxy = True


class LAMetroPost(Post):

    class Meta:
        proxy = True

    @property
    def current_member(self):
        print("method ran")
        if self.memberships.all():
            most_recent_member = self.memberships.order_by(
                '-end_date', '-start_date').first()
            if most_recent_member.end_date:
                return None
            else:
                return most_recent_member
        else:
            return None