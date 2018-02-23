import pytz
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from councilmatic_core.models import Bill, Event, Post, Person, Organization, Action

from .utils import calculate_current_meetings

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

        return self._status(description)

    def _status(self, description):
        if description:
            if description.upper() in ['APPROVED', 'APPROVED AS AMENDED', 'APPROVED THE CONSENT CALENDAR']:
                return 'Approved'
            elif description.upper() in ['ADOPTED', 'ADOPTED AS AMENDED']:
                return 'Adopted'
            elif description.upper() in ['RECOMMENDED FOR APPROVAL', 'RECOMMENDED FOR APPROVAL AS AMENDED', 'REFERRED', 'FORWARDED DUE TO ABSENCES AND CONFLICTS', 'FORWARDED WITHOUT RECOMMENDATION', 'NO ACTION TAKEN', 'NOT DISCUSSED']:
                return 'Active'
            elif description.upper() in ['RECEIVED', 'RECEIVED AND FILED']:
                return 'Received'
            elif description.upper() == 'FAILED':
                return 'Failed'
            elif description.upper() == 'WITHDRAWN':
              return 'Withdrawn'
        else:
            return None

    # LA METRO CUSTOMIZATION
    @property
    def attachments(self):

        return self.documents.all()

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

    @property
    def topics(self):
        return [s.subject for s in self.subjects.all()]

class LAMetroPost(Post):

    class Meta:
        proxy = True

    @property
    def current_members(self):
        today = timezone.now().date()
        return self.memberships.filter(end_date__gte=today)

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
            return self.memberships.all().filter(end_date__gt=datetime.now(app_timezone)).filter(role__contains=settings.COMMITTEE_CHAIR_TITLE).filter(_organization__classification='committee').distinct('_organization')
        else:
            return []

    @property
    def member_role_memberships(self):
        if hasattr(settings, 'COMMITTEE_MEMBER_TITLE'):
            return self.memberships.all().filter(end_date__gt=datetime.now(app_timezone)).filter(role__contains=settings.COMMITTEE_MEMBER_TITLE).filter(_organization__classification='committee').distinct('_organization')
        else:
            return []


class LAMetroEvent(Event):

    class Meta:
        proxy = True

    @classmethod
    def upcoming_board_meeting(cls):
        return cls.objects.filter(start_time__gt=datetime.now(app_timezone))\
                  .filter(name__icontains="Board Meeting")\
                  .exclude(status='cancelled')\
                  .order_by('start_time').first()


    @classmethod
    def current_meeting(cls):
        # Testing....
        fakenow = datetime.now(app_timezone) - timedelta(days=36) - timedelta(hours=6) + timedelta(minutes=45)
        print('NOW: ', fakenow)
        six_minutes_from_now = fakenow + timedelta(minutes=6)
        three_hours_ago = fakenow - timedelta(hours=3)

        # Create the boundaries for discovering events (in progess) within the timeframe stipulated 
        # by Metro.
        # Then, filter the events according to these boundaries.
        # six_minutes_from_now = datetime.now(app_timezone) + timedelta(minutes=6)
        # three_hours_ago = datetime.now(app_timezone) - timedelta(hours=3)

        found_events = cls.objects.filter(start_time__lt=six_minutes_from_now)\
                  .filter(start_time__gt=three_hours_ago)\
                  .exclude(status='cancelled')\
                  .order_by('start_time')

        '''
        Create the boundaries for discovering events (in progess) within the timeframe stipulated 
        by Metro. A meeting displays as current if:
        (1) "now" is six minutes or less before the designated start time;
        (2) the previous meeting has ended (determined by looking for "In progress" on Legistar);

        This method returns a list (with zero or more elements).
        '''
        # six_minutes_from_now = datetime.now(app_timezone) + timedelta(minutes=6)
        # three_hours_ago = datetime.now(app_timezone) - timedelta(hours=6)
        found_events = cls.objects.filter(start_time__lt=six_minutes_from_now)\
                  .filter(start_time__gt=three_hours_ago)\
                  .exclude(status='cancelled')\
                  .order_by('start_time')

        #  Solution 1: calculate the current meeting, given particular parameters, and use Legistar to determine when a meeting has ended.
        if found_events:
            return calculate_current_meetings(found_events, six_minutes_from_now)





        # Solution 2: rely entirely on Legistar.
        # Iterate over all events scheduled within the next six hours, and inspect Legistar for presence of "In progress"
        # PRO: we can eliminate the complex logic for finding and displaying current meetings. 
        # PRO: we do not need to worry about the weirdness of "simultaneous meetings."
        # CON: this solution could add significant load time to the index page, since it has to hit Legistar up to four times. 
        # CON: the Legistar server can be slow to respond (again, causing slowness for loading the Metro home page)
        # CON: the home page may be confusing – meetings can start late (sometimes 30 minutes late), and the dissonance between the start time on the web interface and the current-meeting view may confuse users.

        # if found_events:
        #     for e in events:
        #         organization_name = EventParticipant.objects.get(event_id=e.ocd_id).entity_name
        #         organization_detail_url = Organization.objects.get(name=organization_name).source_url

        #         import requests

        #         r = requests.get(organization_detail_url)
        #         if 'In&amp;nbsp;progress' in r.content.decode('utf-8'):
        #             return e
                


    @classmethod
    def upcoming_committee_meetings(cls):
        meetings = cls.objects.filter(start_time__gt=timezone.now())\
                  .filter(start_time__lt=(timezone.now() + relativedelta(months=1)))\
                  .exclude(name__icontains='Board Meeting')\
                  .order_by('start_time').all()

        if not meetings:
            meetings = cls.objects.filter(start_time__gt=timezone.now())\
                  .filter(start_time__lt=(timezone.now() + relativedelta(months=2)))\
                  .exclude(name__icontains='Board Meeting')\
                  .order_by('start_time').all()


        return meetings