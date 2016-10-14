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
        # Get most recent action.
        action = self.actions.all().order_by('-order').first()
        # Get description of that action.
        description = action.description
        bill_type = self.bill_type

        if bill_type.lower() in ['informational report', 'public hearing', 'minutes', 'appointment', 'oral report / presentation', 'motion / motion response']:
            return None
        elif self._status(description):
            return self._status(description)
        else:
            return None

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
        return False

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