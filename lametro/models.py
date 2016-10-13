from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Person
from datetime import datetime
import pytz

app_timezone = pytz.timezone(settings.TIME_ZONE)

class LAMetroBill(Bill):

    class Meta:
		    proxy = True

    # LA METRO CUSTOMIZATION
    @property
    def friendly_name(self):
        nums_only = self.identifier.split(' ')[-1]
        return self.bill_type+' '+nums_only

    # LA METRO CUSTOMIZATION
    @property
    def inferred_status(self):
        # return 'Active'

        # TODO: Figure out when a bill is active or stale or if this matters at all. Pasted below comes from Chicago.

        actions = self.actions.all().order_by('-order')
        print(actions)
        # classification_hist = [a.classification for a in actions]
        # last_action_date = actions[0].date if actions else None
        # bill_type = self.bill_type

        # if bill_type.lower() in ['communication', 'oath of office']:
        #     return None
        # if self._terminal_status(classification_hist, bill_type):
        #     return self._terminal_status(classification_hist, bill_type)
        # elif self._is_stale(last_action_date):
        #     return 'Stale'
        # else:
        #     return 'Active'

        return "Active"


    # LA METRO CUSTOMIZATION
    @property
    def attachments(self):

        return self.documents.filter(document_type='V').all()
