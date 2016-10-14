from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Event, Post
from datetime import datetime, date
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
        most_recent_member = self.memberships.order_by(
            '-end_date', '-start_date').first()
        if most_recent_member.end_date:
            today = date.today()
            end_date = most_recent_member.end_date
            if today > end_date:
                return None
            else:
                return most_recent_member

    @property
    def formatted_label(self):
        label = self.label
        label_parts = label.split(', ')
        formatted_label = '<br>'.join(label_parts)
        return formatted_label
