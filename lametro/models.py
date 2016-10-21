from django.conf import settings
from django.db import models
from councilmatic_core.models import Bill, Event, Post, Person, Organization
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
        return self.bill_type + ' ' + nums_only

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
            legistar_doc_url = self.documents.filter(document_type='V').first().url
            doc_url = '{0}?filename={2}&document_url={1}'.format(base_url,
                                                                 legistar_doc_url,
                                                                 self.identifier)
            return doc_url
        else:
            return None

    @property
    def controlling_body(self):
        """
        grabs the organization that's currently 'responsible' for a bill
        """

        return self.from_organization

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
            return most_recent_member if today < end_date else None

    @property
    def formatted_label(self):
        label = self.label
        label_parts = label.split(', ')
        formatted_label = '<br>'.join(label_parts)
        return formatted_label

class LAMetroPerson(Person):

    class Meta:
        proxy = True

    @property
    def latest_council_membership(self):
        if hasattr(settings, 'OCD_CITY_COUNCIL_ID'):
            filter_kwarg = {'_organization__ocd_id': settings.OCD_CITY_COUNCIL_ID}
        else:
            filter_kwarg = {'_organization__name': settings.OCD_CITY_COUNCIL_NAME}
        city_council_memberships = self.memberships.filter(**filter_kwarg)
        if city_council_memberships.count():
            return city_council_memberships.order_by('-end_date').first()
        return None

    @property
    def current_council_seat(self):
        '''
        current_council_seat operated on assumption that board members
        represent a jurisdiction; that's not the case w la metro. just
        need to know whether member is current or not...
        '''
        m = self.latest_council_membership
        if m:
            end_date = m.end_date
            today = date.today()
            return True if today < end_date else False
        return None

    @property
    def latest_council_seat(self):
        pass

    @property
    def committee_sponsorships(self):
        '''
        should we omit 'board of directors' as a committee?
        they are primary sponsor of a lot of activity, so the first
        10 items in this feed looks p much the same for every member
        and is thus not that useful, whereas committee-specific
        feeds are a bit more distinctive (altho committees seem
        to sponsor much less legislation... with the most recent
        being from february - do they only meet at certain times?)
        '''
        m = self.memberships.all()
        if m:
            oids = [o._organization_id for o in m]
            # uncomment next line to omit board of directors from feed
            oids.remove(Organization.objects.filter(name='Board of Directors')[0].ocd_id)
            leg = []
            for id_ in oids:
                try:
                    committee = Organization.objects.filter(ocd_id=id_)[0]
                    leg += committee.recent_activity
                except IndexError: # handle errant oid in my db; pls resolve
                    pass
            return leg
        return None