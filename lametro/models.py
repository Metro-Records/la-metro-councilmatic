from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Event, Post, Person
from datetime import datetime, date
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
        # Get most recent action.
        action = self.actions.all().order_by('-order').first()

        # Get description of that action.
        if action:
            description = action.description
        else:
            description = ''

        bill_type = self.bill_type

        if bill_type.lower() in ['informational report', 'public hearing', 'appointment', 'oral report / presentation']:
            return None
        else:
            return self._status(description)

 # def inferred_status(self):
 #        actions = self.actions.all().order_by('-order')
 #        classification_hist = [a.classification for a in actions]
 #        last_action_date = actions[0].date if actions else None
 #        bill_type = self.bill_type

 #        if bill_type.lower() in ['communication', 'oath of office']:
 #            return None
 #        if self._terminal_status(classification_hist, bill_type):
 #            return self._terminal_status(classification_hist, bill_type)
 #        elif self._is_stale(last_action_date):
 #            return 'Stale'
 #        else:
 #            return 'Active'



    def _status(self, description):
        if description:
            if 'approved' in description.lower():
                return 'Approved'
            elif 'adopted' in description.lower():
                return 'Adopted'
            elif description.lower() in ['recommended', 'discussed', 'referred', 'forwarded']:
                return 'Active'
            elif 'withdrawn' in description.lower():
              return 'Withdrawn'
        else:
            return None

    # LA METRO CUSTOMIZATION
    @property
    def attachments(self):

        return self.documents.filter(document_type='V').all()

    # LA METRO CUSTOMIZATION
    @property
    def full_text_doc_url(self):
        base_url = 'https://pic.datamade.us/lametro/document/'
        # base_url = 'http://127.0.0.1:5000/lametro/document/'

        if self.documents.filter(document_type='V').all():
            legistar_doc_url = self.documents.filter(document_type='V').first().document.url
            doc_url = '{0}?filename={2}&document_url={1}'.format(base_url,
                                                                 legistar_doc_url,
                                                                 self.identifier)
            return doc_url
        else:
            return None

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

