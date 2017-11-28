import pytz
import re
from datetime import datetime, timedelta

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
        # A board meeting lasts 3 hours, and a committee event lasts 1 hour.
        # Find all events occuring in the next three hours, and then filter accordingly. 
        meeting_time = datetime.now(app_timezone) + timedelta(minutes=6)
        meeting_end_time = datetime.now(app_timezone) - timedelta(hours=3)

        found_events = cls.objects.filter(start_time__lt=meeting_time)\
                  .filter(start_time__gt=meeting_end_time)\
                  .exclude(status='cancelled')\
                  .order_by('start_time')

        if found_events:
            # Is there more than one event going on?
            if len(found_events) > 1: 
                return calculate_current_meetings(found_events, meeting_time)   
            else:
                if "Committee" in found_events.first().name:
                    meeting_end_time = meeting_time - timedelta(hours=1)
                        
                    return cls.objects.filter(start_time__lt=meeting_time)\
                              .filter(start_time__gt=meeting_end_time)\
                              .exclude(status='cancelled')\
                              .order_by('start_time').first()
                
                else:
                    return found_events.first()


    @classmethod
    def upcoming_committee_meetings(cls):
        meetings = cls.objects.filter(start_time__gt=timezone.now())\
                  .filter(start_time__lt=datetime(timezone.now().year, timezone.now().month+1, 1))\
                  .exclude(name__icontains='Board Meeting')\
                  .order_by('start_time').all()

        if not meetings:
            meetings = cls.objects.filter(start_time__gt=timezone.now())\
                  .filter(start_time__lt=datetime(timezone.now().year, timezone.now().month+2, 1))\
                  .exclude(name__icontains='Board Meeting')\
                  .order_by('start_time').all()

        return meetings