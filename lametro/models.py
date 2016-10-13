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
        # TODO: Figure out when a bill is active or stale or if this matters at all. Pasted below comes from Chicago.
        # We can expect only one action per bill. LA Metro does not provide a robust history.
        actions = self.actions.all().order_by('-order')

        description_hist = [a.description for a in actions]

        last_action_date = actions[0].date if actions else None

        bill_type = self.bill_type

        if bill_type.lower() in ['informational report', 'public hearing', 'minutes', 'appointment', 'oral report / presentation', 'motion / motion response']:
            return None
        # if self._terminal_status(classification_hist, bill_type):
        #     return self._terminal_status(classification_hist, bill_type)
        # elif self._is_stale(last_action_date):
        #     return 'Stale'
        else:
            return 'Active'

    # LA METRO CUSTOMIZATION
    @property
    def attachments(self):

        return self.documents.filter(document_type='V').all()

    # LA METRO CUSTOMIZATION
    @property
    def full_text_doc_url(self):
        # base_url = 'https://pic.datamade.us/lametro/document/'
        base_url = 'http://127.0.0.1:8000/pdfviewer/'

        if self.documents.filter(document_type='V').all():
            legistar_doc_url = self.documents.filter(document_type='V').first().document.url
            doc_url = '{0}?filename={2}&document_url={1}'.format(base_url,
                                                                 legistar_doc_url,
                                                                 self.identifier)
            return ({ 'legistar_doc_url': legistar_doc_url,
              'doc_url': doc_url})
        else:
            return None