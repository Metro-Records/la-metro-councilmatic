import pytz
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db import models
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.contrib.auth.models import User

import requests

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


class LiveMediaMixin(object):
    BASE_MEDIA_URL = 'http://metro.granicus.com/mediaplayer.php?'
    GENERIC_ENGLISH_MEDIA_URL = BASE_MEDIA_URL + 'camera_id=3'
    GENERIC_SPANISH_MEDIA_URL = BASE_MEDIA_URL + 'camera_id=2'


    @property
    def bilingual(self):
        '''
        Upstream, when an English-language event can be paired with a Spanish-
        language event, the GUID of the Spanish-language event is added to the
        extras dictionary, e.g., return True if the sap_guid is present, else
        return False.
        '''
        return bool(self.extras.get('sap_guid'))


    def _valid(self, media_url):
        response = requests.get(media_url)

        if response.ok and 'The event you selected is not currently in progress' not in response.text:
            return True
        else:
            return False


    @property
    def english_live_media_url(self):
        guid = self.extras['guid']
        english_url = self.BASE_MEDIA_URL + 'event_id={guid}'.format(guid=guid)

        if self._valid(english_url):
            return english_url
        else:
            return self.GENERIC_ENGLISH_MEDIA_URL


    @property
    def spanish_live_media_url(self):
        '''
        If there is not an associated Spanish event, there will not be
        Spanish audio for the event, e.g., return None.
        '''
        if self.bilingual:
            guid = self.extras['sap_guid']
            spanish_url = self.BASE_MEDIA_URL + 'event_id={guid}'.format(guid=guid)

            if self._valid(spanish_url):
                return spanish_url
            else:
                return self.GENERIC_SPANISH_MEDIA_URL

        else:
            return None


class LAMetroEvent(Event, LiveMediaMixin):
    objects = LAMetroEventManager()

    class Meta:
        proxy = True


    @classmethod
    def upcoming_board_meeting(cls):
        return cls.objects.filter(start_time__gt=datetime.now(app_timezone), name__icontains='Board Meeting')\
                          .exclude(status='cancelled')\
                          .order_by('start_time')\
                          .first()


    @staticmethod
    def _time_ago(**kwargs):
        '''
        Convenience method for returning localized, negative timedeltas.
        '''
        return datetime.now(app_timezone) - timedelta(**kwargs)


    @staticmethod
    def _time_from_now(**kwargs):
        '''
        Convenience method for returning localized, positive timedeltas.
        '''
        return datetime.now(app_timezone) + timedelta(**kwargs)


    @classmethod
    def _potentially_current_meetings(cls):
        '''
        Return meetings that could be "current" – that is, meetings that are
        scheduled to start in the last six hours, or in the next five minutes.

        Fun fact: The longest Metro meeting on record is 5.38 hours long (see
        issue #251). Hence, we check for meetings scheduled to begin up to six
        hours ago.

        Used to determine whether to check Granicus for streaming meetings.
        '''
        six_hours_ago = cls._time_ago(hours=6)
        five_minutes_from_now = cls._time_from_now(minutes=5)

        return cls.objects.filter(start_time__gte=six_hours_ago,
                                  start_time__lte=five_minutes_from_now)\
                           .exclude(status='cancelled')


    @classmethod
    def _streaming_meeting(cls):
        '''
        Granicus provides a running events endpoint that returns an array of
        GUIDs for streaming meetings. Metro events occur one at a time, but two
        GUIDs appear when an event is live: one for the English audio, and one
        for the Spanish audio.

        Hit the endpoint, and return the corresponding event, or an empty
        queryset.
        '''
        running_events = requests.get('http://metro.granicus.com/running_events.php')

        for guid in running_events.json():
            # We get back two GUIDs, but we won't know which is the English
            # audio GUID stored in the 'guid' field of the extras dict. Thus,
            # we iterate.
            meeting = cls.objects.filter(extras__guid=guid.upper())

            if meeting:
                return meeting

        return cls.objects.none()


    @classmethod
    def current_meeting(cls):
        '''
        If there is a meeting scheduled to begin in the last six hours or in
        the next five minutes, hit the running events endpoint. If there is a
        running event, return the corresponding meeting. If there are no running
        events, return meetings scheduled to begin in the last 20 minutes (to
        account for late starts) or the next five minutes (to show meetings as
        current, five minutes ahead of time).

        Otherwise, return an empty queryset.
        '''
        scheduled_meetings = cls._potentially_current_meetings()

        if scheduled_meetings:
            streaming_meeting = cls._streaming_meeting()

            if streaming_meeting:
                return streaming_meeting

            twenty_minutes_ago = cls._time_ago(minutes=20)

            # '.annotate' adds a boolean field, 'is_board_meeting'. We want to
            # show board meetings first, so order in reverse, since False (0)
            # comes before True (1).
            return scheduled_meetings.filter(start_time__gte=twenty_minutes_ago)\
                                     .annotate(is_board_meeting=RawSQL("name like %s", ('%Board Meeting%',)))\
                                     .order_by('-is_board_meeting')

        else:
            return cls.objects.none()


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
        '''
        EventMedia imported prior to django-councilmatic 0.10.0 may not have
        an associated note.
        '''
        if self.note and self.note.endswith('(SAP)'):
            return 'Ver en Español'
        else:
            return 'Watch in English'


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
