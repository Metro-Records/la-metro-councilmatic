import pytz
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from councilmatic_core.models import Bill, Event, Post, Person, Organization, \
    Action, EventMedia

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


class LAMetroEventManager(models.Manager):
    def get_queryset(self):
        '''
        If SHOW_TEST_EVENTS is False, omit them from the initial queryset.

        NOTE: Be sure to use LAMetroEvent, rather than the base Event class,
        when getting event querysets. If a test event slips through, it is
        likely because we used the default Event to get the queryset.
        '''
        if not settings.SHOW_TEST_EVENTS:
            return super().get_queryset().exclude(location_name='TEST')

        return super().get_queryset()


class LAMetroEvent(Event):
    objects = LAMetroEventManager()

    class Meta:
        proxy = True

    @classmethod
    def upcoming_board_meeting(cls):
        return cls.objects.filter(start_time__gt=datetime.now(app_timezone), name__icontains='Board Meeting')\
                          .exclude(status='cancelled')\
                          .order_by('start_time')\
                          .first()


    @classmethod
    def current_meeting(cls):

        '''
        Create the boundaries for discovering events (in progess) within the timeframe stipulated 
        by Metro. A meeting displays as current if:
        (1) "now" is five minutes or less before the designated start time;
        (2) the previous meeting has ended (determined by looking for "In progress" on Legistar).

        The maximum recorded meeting duration is 5.38 hours, according to the spreadsheet provided by 
        Metro in issue #251.
        So, to determine initial list of possible current events, we look for all events scheduled 
        in the past 6 hours.

        This method returns a list (with zero or more elements).

        To hardcode current event(s) for testing, use these examples:
        return LAMetroEvent.objects.filter(start_time='2017-06-15 13:30:00-05')
        return LAMetroEvent.objects.filter(start_time='2017-11-30 11:00:00-06')
        '''
        from .utils import calculate_current_meetings  # Avoid circular import

        five_minutes_from_now = datetime.now(app_timezone) + timedelta(minutes=5)
        six_hours_ago = datetime.now(app_timezone) - timedelta(hours=6)
        found_events = cls.objects.filter(start_time__lte=five_minutes_from_now, start_time__gte=six_hours_ago)\
                                  .exclude(status='cancelled')\
                                  .order_by('start_time')

        if found_events:
            return calculate_current_meetings(found_events, five_minutes_from_now)


    @classmethod
    def upcoming_committee_meetings(cls):
        one_month_from_now = timezone.now() + relativedelta(months=1)
        meetings = cls.objects.filter(start_time__gt=timezone.now(), start_time__lt=one_month_from_now)\
                              .exclude(name__icontains='Board Meeting')\
                              .order_by('start_time').all()

        if not meetings:
            two_months_from_now = timezone.now() + relativedelta(months=2)
            meetings = cls.objects.filter(start_time__gt=timezone.now(), start_time__lt=two_months_from_now)\
                                  .exclude(name__icontains='Board Meeting')\
                                  .order_by('start_time').all()

        return meetings

    @property
    def media(self):
        return LAMetroEventMedia.objects.filter(event_id=self.ocd_id)


class LAMetroEventMedia(EventMedia):

    class Meta:
        proxy = True

    @property
    def label(self):
        if self.note.endswith('(SAP)'):
            return 'Escucha'
        else:
            return 'Listen'


class LAMetroOrganization(Organization):
    '''
    Overrides use the LAMetroEvent object, rather than the default Event
    object, so test events are hidden appropriately.
    '''
    class Meta:
        proxy = True

    @property
    def recent_events(self):
        events = LAMetroEvent.objects.filter(participants__entity_type='organization', participants__entity_name=self.name)
        events = events.order_by('-start_time').all()
        return events

    @property
    def upcoming_events(self):
        """
        grabs events in the future
        """
        events = LAMetroEvent.objects\
                             .filter(participants__entity_type='organization', participants__entity_name=self.name)\
                             .filter(start_time__gt=datetime.now(app_timezone))\
                             .order_by('start_time')\
                             .all()
        return events
