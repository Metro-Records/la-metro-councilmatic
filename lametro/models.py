import pytz
import re

from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from councilmatic_core.models import Bill, Event, Post, Person, Organization, Action

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

    @property
    def controlling_body(self):

        return self.from_organization

    def get_last_action_date(self):
        actions = Action.objects.filter(_bill_id=self.ocd_id)

        try:
          action = actions.reverse()[0].date
        except:
          action = ''

        return action

class LAMetroPost(Post):

    class Meta:
        proxy = True

    @property
    def current_members(self):
        today = timezone.now().date()
        return self.memberships.filter(end_date__gte=today)

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
            today = timezone.now().date()
            return True if today < end_date else False
        return None

    @property
    def current_district(self):
        m = self.latest_council_membership
        if m and m.post:
            return m.post.label
        return ''

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

        m = self.memberships.all().filter( _organization__classification='committee').distinct('_organization')

        if m:
            oids = [o._organization_id for o in m]

            leg = []
            for id_ in oids:
                try:
                    committee = Organization.objects.filter(ocd_id=id_)[0]
                    leg += committee.recent_activity
                except IndexError: # handle errant oid in my db; pls resolve
                    pass
            return leg
        return None

    @property
    def chair_role_memberships(self):
        if hasattr(settings, 'COMMITTEE_CHAIR_TITLE'):
            # Keep comments, in case we want to remove AD-HOC.
            # today = timezone.now().date()
            # return self.memberships.all().filter(end_date__gte=today, role__contains=settings.COMMITTEE_CHAIR_TITLE).filter( _organization__classification='committee').distinct('_organization')
            return self.memberships.all().filter(role__contains=settings.COMMITTEE_CHAIR_TITLE).filter( _organization__classification='committee').distinct('_organization')
        else:
            return []

    @property
    def member_role_memberships(self):
        if hasattr(settings, 'COMMITTEE_MEMBER_TITLE'):
            return self.memberships.all().filter(role__contains=settings.COMMITTEE_MEMBER_TITLE).filter( _organization__classification='committee').distinct('_organization')
        else:
            return []

class LAMetroEvent(Event):

    class Meta:
        proxy = True

    @classmethod
    def upcoming_board_meeting(cls):
        return cls.objects.filter(start_time__gt=datetime.now(app_timezone))\
                  .filter(name__icontains="Board of Directors")\
                  .order_by('start_time').first()


        # USED TO TEST THE CURRENT BOARD MEETING METHOD. Keep for now.
        # faketime = datetime.now(app_timezone) + timedelta(days=37) - timedelta(hours=2)

        # return cls.objects.filter(start_time__gt=faketime)\
        #           .filter(name__icontains="Board of Directors")\
        #           .order_by('start_time').first()

    @classmethod
    def current_board_meeting(cls):
        meeting_time = datetime.now(app_timezone) - timedelta(hours=3)

        return cls.objects.filter(start_time__lt=timezone.now())\
                  .filter(start_time__gt=meeting_time)\
                  .filter(name__icontains="Board of Directors")\
                  .order_by('start_time').first()

        # USED TO TEST THE CURRENT BOARD MEETING METHOD. Keep for now.
        # faketime = datetime.now(app_timezone) + timedelta(days=37) - timedelta(hours=2)
        # meeting_time = faketime - timedelta(hours=3)

        # return cls.objects.filter(start_time__lt=faketime)\
        #           .filter(start_time__gt=meeting_time)\
        #           .filter(name__icontains="Board of Directors")\
        #           .order_by('start_time').first()