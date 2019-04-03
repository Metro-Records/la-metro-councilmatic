import pytz
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

from django.conf import settings
from django.db import models, connection
from django.db.models.expressions import RawSQL
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Max, Min, Prefetch, Case, When, Value, Q

from councilmatic_core.models import Bill, Event, Post, Person, Organization, \
    Action, EventMedia, EventDocument


app_timezone = pytz.timezone(settings.TIME_ZONE)


class LAMetroBillManager(models.Manager):
    def get_queryset(self):
        '''
        The Councilmatic database contains both "private" and "public" bills. 
        This issue thread explains why: 
        https://github.com/datamade/la-metro-councilmatic/issues/345#issuecomment-455683240
        
        We do not display "private" bills in Councilmatic.
        Metro staff devised three checks for knowing when to hide or show a report:

        (1) Is the bill private (i.e., `restrict_view` is True)? Then, do not show it.
        N.b., the scrapers contain logic for populating the restrict_view field:
        https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/bills.py

        (2) Does the Bill have a classification of "Board Box"? Then, show it.

        (3) Is the Bill on a published agenda, i.e., an event with the 
        status of "passed" or "cancelled"? Then, show it.

        NOTE! A single bill can appear on multiple event agendas.
        We thus call 'distinct' on the below query, otherwise
        the queryset would contain duplicate bills. 

        WARNING! Be sure to use LAMetroBill, rather than the base Bill class,
        when getting bill querysets. Otherwise restricted view bills
        may slip through the crevices of Councilmatic display logic.
        '''
        filtered_qs = super().get_queryset().exclude(restrict_view=True)\
                                            .filter(Q(related_agenda_items__event__status='passed') | \
                                                    Q(related_agenda_items__event__status='cancelled') | \
                                                    Q(bill_type='Board Box'))\
                                            .distinct()

        return filtered_qs


class LAMetroBill(Bill):
    objects = LAMetroBillManager()

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
        '''
        Several Metro bills do not have "histories."
        Discussed in this issue:
        https://github.com/datamade/la-metro-councilmatic/issues/340

        If a bill does not have a history, then determine its `last_action_date` by
        looking for the most recent agenda that references the bill. Consider only
        events that have already occurred, so the last action date is not in the
        future.
        '''
        actions = Action.objects.filter(_bill_id=self.ocd_id)
        last_action_date = ''

        if actions:
            last_action_date = actions.reverse()[0].date
        else:
            events = Event.objects.filter(agenda_items__bill_id=self.ocd_id,
                                          start_time__lt=timezone.now())

            if events:
                last_action_date = events.latest('start_time').start_time

        return last_action_date

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
        This property returns a list of ten bills, which have recent actions
        from the organizations that the person has memberships in.

        Organizations do not include the Board of Directors.
        '''
        query = '''
            SELECT bill_id
            FROM councilmatic_core_bill as bill
            JOIN councilmatic_core_action as action
            ON bill.ocd_id = action.bill_id
            JOIN councilmatic_core_organization as org
            ON org.ocd_id = action.organization_id
            JOIN councilmatic_core_membership as membership
            ON org.ocd_id = membership.organization_id
            WHERE membership.person_id='{person}'
            AND action.date >= membership.start_date
            AND org.classification = 'committee'
            ORDER BY action.date DESC
            LIMIT 10
        '''.format(person=self.ocd_id)

        with connection.cursor() as cursor:
            cursor.execute(query)
            bill_ids = [bill_tup[0] for bill_tup in cursor.fetchall()]

            bills = LAMetroBill.objects.filter(ocd_id__in=bill_ids)

        return bills


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

    def with_media(self):
        '''
        This function proves useful in the EventDetailView 
        and EventsView (which returns all Events – often, filtered and sorted).

        We prefetch EventMedia (i.e., 'media_urls') in these views: 
        this makes for a more efficient page load. 
        We also order the 'media_urls' by label, ensuring that links to SAP audio
        come after links to English audio. 'mediaqueryset' facilitates 
        the ordering of prefetched 'media_urls'.
        '''
        mediaqueryset = LAMetroEventMedia.objects.annotate(
            olabel=Case(
                When(note__endswith='(SAP)', then=Value(0)),
                output_field=models.CharField(),
            )
        ).order_by('-olabel')

        return self.prefetch_related(Prefetch('media_urls', queryset=mediaqueryset))


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

        Hit the endpoint, and return the corresponding meeting, or an empty
        queryset.
        '''
        running_events = requests.get('http://metro.granicus.com/running_events.php')

        for guid in running_events.json():
            # We get back two GUIDs, but we won't know which is the English
            # audio GUID stored in the 'guid' field of the extras dict. Thus,
            # we iterate.
            #
            # Note that our stored GUIDs are all uppercase, because they come
            # that way from the Legistar API. The running events endpoint
            # returns all-lowercase GUIDs, so we need to uppercase them for
            # comparison.
            meeting = cls.objects.filter(extras__guid=guid.upper())

            if meeting:
                return meeting

        return cls.objects.none()


    @classmethod
    def current_meeting(cls):
        '''
        If there is a meeting scheduled to begin in the last six hours or in
        the next five minutes, hit the running events endpoint.

        If there is a running event, return the corresponding meeting.

        If there are no running events, return meetings scheduled to begin in
        the last 20 minutes (to account for late starts) or in the next five
        minutes (to show meetings as current, five minutes ahead of time).

        Otherwise, return an empty queryset.
        '''
        scheduled_meetings = cls._potentially_current_meetings()

        if scheduled_meetings:
            streaming_meeting = cls._streaming_meeting()

            if streaming_meeting:
                current_meetings = streaming_meeting

            else:
                # Sometimes, streams start later than a meeting's start time.
                # Check for meetings scheduled to begin in the last 20 minutes
                # so they are returned as current in the event that the stream
                # does not start on time.
                #
                # Note that 'scheduled_meetings' already contains meetings
                # scheduled to start in the last six hours or in the next five
                # minutes, so we just need to add the 20-minute lower bound to
                # return meetings scheduled in the last 20 minutes or in the
                # next five minutes.
                twenty_minutes_ago = cls._time_ago(minutes=20)

                # '.annotate' adds a boolean field, 'is_board_meeting'. We want
                # to show board meetings first, so order in reverse, since False
                # (0) comes before True (1).
                current_meetings = scheduled_meetings.filter(start_time__gte=twenty_minutes_ago)\
                                                     .annotate(is_board_meeting=RawSQL("name like %s", ('%Board Meeting%',)))\
                                                     .order_by('-is_board_meeting')

        else:
            current_meetings = cls.objects.none()

        return current_meetings


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
    def event_minutes(self):
        '''
        This method returns the link to an Event's minutes. 

        A small number of Events do not have minutes in a corresponding
        LAMetroBill. For these, we can query for an EventDocument and 
        return its link. 
        '''
        date = self.start_time.date().strftime('%B %d, %Y')
        content = 'minutes of the regular board meeting held ' + date
        try:
            import pdb; pdb.set_trace()
            board_report = LAMetroBill.objects.get(ocr_full_text__icontains=content, bill_type='Minutes')
        except LAMetroBill.DoesNotExist:
            try:
                doc = self.documents.get(note__icontains='RBM Minutes')
            except EventDocument.DoesNotExist:
                return None
            else:
                return doc.url
        else:
            return '/board-report/' + board_report.slug


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
