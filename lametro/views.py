import re
from itertools import groupby
from operator import attrgetter
import itertools
import urllib
import json
from datetime import date, timedelta, datetime, MINYEAR
from dateutil.relativedelta import relativedelta
from dateutil import parser
import requests
import sqlalchemy as sa
from collections import namedtuple
import json as simplejson
import os

from haystack.inputs import Raw
from haystack.query import SearchQuerySet

import pytz

from django.db import transaction, connection, connections
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
from django.db.models.functions import Lower, Now, Cast
from django.db.models import Max, Min, Prefetch, Case, When, Value, IntegerField
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response, redirect
from django.core import management
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from councilmatic_core.views import IndexView, BillDetailView, \
    CouncilMembersView, AboutView, CommitteeDetailView, CommitteesView, \
    PersonDetailView, EventDetailView, EventsView, CouncilmaticFacetedSearchView, \
    CouncilmaticSearchForm
from councilmatic_core.models import *

from lametro.models import LAMetroBill, LAMetroPost, LAMetroPerson, \
    LAMetroEvent, LAMetroOrganization
from lametro.forms import AgendaUrlForm, AgendaPdfForm

from councilmatic.settings_jurisdiction import MEMBER_BIOS
from councilmatic.settings import MERGER_BASE_URL, PIC_BASE_URL

from opencivicdata.legislative.models import EventDocument

app_timezone = pytz.timezone(settings.TIME_ZONE)

class LAMetroIndexView(IndexView):
    template_name = 'lametro/index.html'

    event_model = LAMetroEvent

    @property
    def extra_context(self):
        extra = {}
        extra['upcoming_board_meeting'] = self.event_model.upcoming_board_meeting()
        extra['current_meeting'] = self.event_model.current_meeting()
        extra['bilingual'] = bool([e for e in extra['current_meeting'] if e.bilingual])

        return extra

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = self.get_object().actions.all().order_by('-order')
        context['attachments'] = self.get_object().attachments.all().order_by(Lower('note'))

        context['board_report'] = self.get_object().versions.get(note="Board Report")
        item = context['legislation']
        actions = self.get_object().actions.all()
        organization_lst = [action.organization for action in actions]
        context['sponsorships'] = set(organization_lst)

        # Create URL for packet download.
        packet_slug = item.id.replace('/', '-')
        try:
            r = requests.head(MERGER_BASE_URL + '/document/' + packet_slug)
            if r.status_code == 200:
                context['packet_url'] = MERGER_BASE_URL + '/document/' + packet_slug
        except:
            context['packet_url'] = None

        related_bills = context['legislation']\
            .related_bills\
            .annotate(latest_date=Max('related_bill__actions__date'))\
            .order_by('-latest_date')

        context['related_bills'] = related_bills

        return context


class LAMetroEventDetail(EventDetailView):
    model = LAMetroEvent
    template_name = 'lametro/event.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() # Assign object to detail view, so that get_context_data can find this variable: https://stackoverflow.com/questions/34460708/checkoutview-object-has-no-attribute-object
        event = self.get_object()
        event_slug = event.slug

        # Look for the button name and assign form values.
        if 'url_form' in request.POST:
            url_form = AgendaUrlForm(request.POST)
            pdf_form = AgendaPdfForm()
        elif 'pdf_form' in request.POST:
            pdf_form = AgendaPdfForm(request.POST, request.FILES)
            url_form = AgendaUrlForm()

        # Validate forms and redirect.
        if url_form.is_valid():
            agenda_url = url_form['agenda'].value()
            document_obj, created = EventDocument.objects.get_or_create(event=event,
                url=agenda_url, updated_at= timezone.now())
            document_obj.note = ('Event Document - Manual upload URL')
            document_obj.save()

            return HttpResponseRedirect('/event/%s' % event_slug)
        elif pdf_form.is_valid() and 'pdf_form' in request.POST:
            agenda_pdf = request.FILES['agenda']

            handle_uploaded_agenda(agenda=agenda_pdf, event=event)

            return HttpResponseRedirect('/event/%s' % event_slug)
        else:
            return self.render_to_response(self.get_context_data(url_form=url_form, pdf_form=pdf_form))

    def get_object(self):
        # Get the event with prefetched media_urls in proper order.
        event = LAMetroEvent.objects.with_media().get(slug=self.kwargs['slug'])

        return event

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        event = context['event']

        # Metro admins should see a status report if Legistar is down.
        # GET the calendar page, which contains relevant URL for agendas.
        if self.request.user.is_authenticated:
            r = requests.get('https://metro.legistar.com/calendar.aspx')
            context['legistar_ok'] = r.ok

        # Create URL for packet download.
        packet_slug = event.id.replace('/', '-')
        try:
            r = requests.head(MERGER_BASE_URL + '/document/' + packet_slug)
            if r.status_code == 200:
                context['packet_url'] = MERGER_BASE_URL + '/document/' + packet_slug
            elif r.status_code == 404:
                context['packet_url'] = None
        except:
            context['packet_url'] = None

        agenda_with_board_reports = event.agenda\
            .filter(related_entities__bill__versions__isnull=False)\
            .annotate(int_order=Cast('order', IntegerField()))\
            .order_by('int_order')
        
        # Find agenda link.
        if event.documents.all():
            for document in event.documents.all():
                if "Agenda" in document.note:
                    context['agenda_url'] = document.links.first().url
                    context['document_timestamp'] = document.date
                elif "Manual upload URL" in document.note:
                    context['uploaded_agenda_url'] = document.links.first().url
                    context['document_timestamp'] = document.date
                elif "Manual upload PDF" in document.note:
                    context['uploaded_agenda_pdf'] = document.links.first().url
                    context['document_timestamp'] = document.date
                    '''
                    LA Metro Councilmatic uses the adv_cache library
                    to partially

                    cache templates: in the event view, we cache the
                    entire template, except the iframe. (N.B. With
                    this library, the views do not cached, unless
                    explicitly wrapped in a django cache decorator.
                    Nonetheless, several popular browsers (e.g.,
                    Chrome and Firefox) retrieve cached iframe images,
                    regardless of the site's caching specifications.
                    We use the agenda's "updated_at" timestamp to bust
                    the iframe cache: we save it inside context and
                    then assign it as the "name" of the iframe,
                    preventing the browser from retrieving a cached
                    iframe, when the timestamp changes.
                    '''

        context['related_board_reports'] = agenda_with_board_reports
        context['base_url'] = PIC_BASE_URL # Give JS access to this variable

        # Render forms if not a POST request
        if 'url_form' not in context:
            context['url_form'] = AgendaUrlForm()
        if 'pdf_form' not in context:
            context['pdf_form'] = AgendaPdfForm()

        return context


def handle_uploaded_agenda(agenda, event):
    with open('lametro/static/pdf/agenda-%s.pdf' % event.slug, 'wb+') as destination:
        for chunk in agenda.chunks():
            destination.write(chunk)

    # Create the document in database
    document_obj, created = EventDocument.objects.get_or_create(event=event,
        url='pdf/agenda-%s.pdf' % event.slug, updated_at= timezone.now())
    document_obj.note = ('Event Document - Manual upload PDF')
    document_obj.save()

    # Collect static to render PDF on server
    management.call_command('collectstatic', '--noinput')


def delete_submission(request, event_slug):
    event = LAMetroEvent.objects.get(slug=event_slug)
    event_doc = EventDocument.objects.filter(event_id=event.id, note__icontains='Manual upload')

    for e in event_doc:
        # Remove stored PDF from Metro app.
        if 'Manual upload PDF' in e.note:
            try:
                os.remove('lametro/static/%s' % e.url )
            except OSError:
                pass
        e.delete()

    return HttpResponseRedirect('/event/%s' % event_slug)


class LAMetroEventsView(EventsView):
    template_name = 'lametro/events.html'

    def get_context_data(self, **kwargs):
        context = {}

        # Did the user set date boundaries?
        start_date_str = self.request.GET.get('from')
        end_date_str   = self.request.GET.get('to')
        day_grouper    = lambda x: (x.start_time.year, x.start_time.month, x.start_time.day)

        minutes_queryset = EventDocument.objects.filter(note__icontains='minutes')

        # If yes...
        if start_date_str and end_date_str:
            context['start_date'] = start_date_str
            context['end_date']   = end_date_str
            start_date_time       = parser.parse(start_date_str)
            end_date_time         = parser.parse(end_date_str)

            select_events = LAMetroEvent.objects\
                                        .with_media()\
                                        .filter(start_time__gt=start_date_time)\
                                        .filter(start_time__lt=end_date_time)\
                                        .order_by('start_time')\

            select_events = select_events.prefetch_related(Prefetch('documents',
                                                                minutes_queryset,
                                                                to_attr='minutes'))\
                                         .prefetch_related('minutes__links')

            org_select_events = []

            for event_date, events in itertools.groupby(select_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_select_events.append([date(*event_date), events])

            context['select_events'] = org_select_events

        # If all meetings
        elif self.request.GET.get('show'):
            all_events = LAMetroEvent.objects\
                                     .with_media()\
                                     .order_by('-start_time')\

            org_all_events = []

            for event_date, events in itertools.groupby(all_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_all_events.append([date(*event_date), events])

            context['all_events'] = org_all_events
        # If no...
        else:
            # Upcoming events
            future_events = LAMetroEvent.objects\
                                        .with_media()\
                                        .filter(start_time__gt=timezone.now())\
                                        .order_by('start_time')\

            org_future_events = []

            for event_date, events in itertools.groupby(future_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_future_events.append([date(*event_date), events])

            context['future_events'] = org_future_events

            # Past events
            past_events = LAMetroEvent.objects\
                                      .with_media()\
                                      .filter(start_time__lt=datetime.datetime.now(app_timezone))\
                                      .order_by('-start_time')

            past_events = past_events.prefetch_related(Prefetch('documents',
                                                                minutes_queryset,
                                                                to_attr='minutes'))\
                                     .prefetch_related('minutes__links')

            org_past_events = []

            for event_date, events in itertools.groupby(past_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_past_events.append([date(*event_date), events])

            context['past_events'] = org_past_events

        context['user_subscribed'] = False
        if self.request.user.is_authenticated:
            user = self.request.user
            context['user'] = user

            if settings.USING_NOTIFICATIONS:
                if (len(user.eventssubscriptions.all()) > 0):
                    context['user_subscribed'] = True

        return context

class LABoardMembersView(CouncilMembersView):
    template_name = 'lametro/board_members.html'

    def map(self):
        map_geojson = {
            'type': 'FeatureCollection',
            'features': []
        }

        map_geojson_sectors = {
            'type': 'FeatureCollection',
            'features': []
        }

        map_geojson_city = {
            'type': 'FeatureCollection',
            'features': []
        }

        for post in self.object_list:
            if post.shape:
                council_member = "Vacant"
                detail_link = ""
                if post.current_members:
                    for membership in post.current_members:
                        council_member = membership.person.name
                        detail_link = membership.person.slug

                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(post.shape),
                    'properties': {
                        'district': post.label,
                        'council_member': council_member,
                        'detail_link': '/person/' + detail_link,
                        'select_id': 'polygon-{}'.format(slugify(post.label)),
                    },
                }

                if 'council_district' in post.division_id:
                    map_geojson['features'].append(feature)

                if 'la_metro_sector' in post.division_id:
                    map_geojson_sectors['features'].append(feature)

                if post.division_id == 'ocd-division/country:us/state:ca/place:los_angeles':
                    map_geojson_city['features'].append(feature)

        context['map_geojson'] = json.dumps(map_geojson)
        context['map_geojson_sectors'] = json.dumps(map_geojson_sectors)
        context['map_geojson_city'] = json.dumps(map_geojson_city)

    def get_queryset(self):
        get_kwarg = {'name': settings.OCD_CITY_COUNCIL_NAME}

        # put family name in scraper
        # fix doubling up of garcetti in scraper
        # ceo's should be removed in the scraper
        return Organization.objects.get(**get_kwarg)\
                                   .memberships\
                                   .filter(end_date_dt__gte=Now())\
                                   .exclude(role='Chief Executive Officer')\
                                   .annotate(role_order=Case(
                                       When(role='Chair', then=Value(1)),
                                       When(role='Vice Chair', then=Value(2)),
                                       When(role='1st Vice Chair', then=Value(2)),
                                       When(role='2nd Vice Chair', then=Value(3)),
                                       When(role='Board Member', then=Value(4)),
                                       When(role='Nonvoting Board Member', then=Value(5)),
                                       output_field=IntegerField()))\
                                   .order_by('role_order', 'person__family_name')

    def get_context_data(self, *args, **kwargs):
        context = super(LABoardMembersView, self).get_context_data(**kwargs)

        board = LAMetroOrganization.objects.get(name=settings.OCD_CITY_COUNCIL_NAME)
        context['recent_activity'] = board.actions.order_by('-date', '-_bill__identifier', '-order')
        context['recent_events'] = board.recent_events

        return context


class LAMetroAboutView(AboutView):
    template_name = 'lametro/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['timestamp'] = datetime.datetime.now(app_timezone).strftime('%m%d%Y%s')

        return context


class LACommitteesView(CommitteesView):
    template_name = 'lametro/committees.html'


class LACommitteeDetailView(CommitteeDetailView):

    model = LAMetroOrganization
    template_name = 'lametro/committee.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        committee = context['committee']

        if getattr(settings, 'COMMITTEE_DESCRIPTIONS', None):
            description = settings.COMMITTEE_DESCRIPTIONS.get(committee.slug)
            context['committee_description'] = description

        with connection.cursor() as cursor:
            base_sql = '''
              SELECT
                m.role,
                p.name, p.slug, p.ocd_id,
                m.extras,
                array_agg(mm.label::VARCHAR)
                FILTER (WHERE mm.label is not Null) as label,
                split_part(p.name, ' ', 2) AS last_name
              FROM councilmatic_core_membership AS m
              LEFT JOIN (
                SELECT
                  person_id,
                  array_agg(DISTINCT pt.label) as label
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_post AS pt
                  ON m.post_id=pt.ocd_id
                WHERE m.organization_id = %s
                GROUP BY person_id
              ) AS mm
                USING(person_id)
              JOIN councilmatic_core_person AS p
                ON m.person_id = p.ocd_id
              WHERE m.organization_id = %s
              AND m.end_date::date > NOW()::date
              AND m.role != 'Chief Executive Officer'
              GROUP BY
                m.role, p.name, p.slug, p.ocd_id, m.extras
              {order_by}
            '''
            committee_sql = base_sql.format(order_by="ORDER BY CASE " +
                                           "WHEN m.role='Chair' THEN 0 " +
                                           "WHEN m.role='Vice Chair' THEN 1 " +
                                           "WHEN m.role='Member' THEN 2" +
                                           "END")

            cursor.execute(committee_sql, [settings.OCD_CITY_COUNCIL_ID, committee.ocd_id])
            columns = [c[0] for c in cursor.description]
            results_tuple = namedtuple('Member', columns)
            objects_list = [results_tuple(*r) for r in cursor]

            context['membership_objects'] = objects_list

            ad_hoc_committee_sql = base_sql.format(order_by="ORDER BY CASE " +
                                           "WHEN m.role='Chair' THEN 0 " +
                                           "WHEN m.role='1st Vice Chair' THEN 1 " +
                                           "WHEN m.role='2nd Vice Chair' THEN 2 "
                                           "WHEN m.role='Member' THEN 3" +
                                           "END")

            cursor.execute(ad_hoc_committee_sql, [settings.OCD_CITY_COUNCIL_ID, committee.ocd_id])

            columns = [c[0] for c in cursor.description]
            results_tuple = namedtuple('Member', columns)
            objects_list = [results_tuple(*r) for r in cursor]

            context['ad_hoc_list'] = objects_list

            context['ceo'] = Person.objects.filter(memberships__role='Chief Executive Officer',                                   memberships___organization=committee.ocd_id).first()

        return context


class LAPersonDetailView(PersonDetailView):

    template_name = 'lametro/person.html'
    model = LAMetroPerson

    def dispatch(self, request, *args, **kwargs):
        slug = self.kwargs['slug']

        try:
            person = self.model.objects.get(slug=slug)

        except LAMetroPerson.DoesNotExist:
            person = None

        else:
            response = super().dispatch(request, *args, **kwargs)

        if not person:
            # Grab the first and last name from slug like "john-smith-af5a8ab39aad"
            short_slug = '-'.join(slug.split('-')[:-1])

            try:
                person = self.model.objects.get(slug__startswith=short_slug)
            except (LAMetroPerson.DoesNotExist, LAMetroPerson.MultipleObjectsReturned):
                # Return a 404 if more than one matching slug, or if there are no matching slugs
                response = HttpResponseNotFound()
            else:
                response = HttpResponsePermanentRedirect(reverse('person', args=[person.slug]))

        return response

    def get_context_data(self, **kwargs):
        post_model = LAMetroPost

        context = super().get_context_data(**kwargs)
        person = context['person']

        title = ''
        qualifying_post = '' # board membership criteria met by person in question
        m = person.latest_council_membership
        if person.current_council_seat:
            title = m.role
            if m.post:
                qualifying_post = m.post.label
                if m.extras.get('acting'):
                    qualifying_post = 'Acting' + ' ' + qualifying_post

        else:
            title = 'Former %s' % m.role
        context['title'] = title
        context['qualifying_post'] = qualifying_post

        if person.committee_sponsorships:
            context['sponsored_legislation'] = person.committee_sponsorships
        else:
            context['sponsored_legislation'] = []

        with connection.cursor() as cursor:

            sql = ('''
                SELECT o.name as organization, o.slug as org_slug, m.role
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_organization AS o
                ON o.ocd_id = m.organization_id
                WHERE m.person_id = %s
                AND m.end_date::date > NOW()::date
                AND m.organization_id != %s
                ORDER BY
                    CASE
                        WHEN m.role='Chair' THEN 0
                        WHEN m.role='Vice Chair' THEN 1
                        WHEN m.role='Member' THEN 2
                    END
                ''')

            cursor.execute(sql, [person.ocd_id, settings.OCD_CITY_COUNCIL_ID])

            columns = [c[0] for c in cursor.description]

            results_tuple = namedtuple('Member', columns)
            memberships_list = [results_tuple(*r) for r in cursor]
            context['memberships_list'] = memberships_list

        if person.slug in MEMBER_BIOS:
            context['member_bio'] = MEMBER_BIOS[person.slug]

        return context


class LAMetroCouncilmaticSearchForm(CouncilmaticSearchForm):
    def __init__(self, *args, **kwargs):
        if kwargs.get('search_corpus'):
            self.search_corpus = kwargs.pop('search_corpus')

        super(LAMetroCouncilmaticSearchForm, self).__init__(*args, **kwargs)

    def search(self):
        sqs = super(LAMetroCouncilmaticSearchForm, self).search()

        if self.search_corpus == 'all':
            # Don't auto-escape my query! https://django-haystack.readthedocs.io/en/v2.4.1/searchqueryset_api.html#SearchQuerySet.filter
            sqs = sqs.filter_or(attachment_text=Raw(self.cleaned_data['q']))

        return sqs


class LAMetroCouncilmaticFacetedSearchView(CouncilmaticFacetedSearchView):
    def __init__(self, *args, **kwargs):
        kwargs['form_class'] = LAMetroCouncilmaticSearchForm
        super(LAMetroCouncilmaticFacetedSearchView, self).__init__(*args, **kwargs)

    def build_form(self, form_kwargs={}):
        form = super(CouncilmaticFacetedSearchView, self).build_form(form_kwargs=form_kwargs)

        form_kwargs['selected_facets'] = self.request.GET.getlist("selected_facets")
        form_kwargs['search_corpus'] = 'all' if self.request.GET.get('search-all') else 'bills'

        sqs = SearchQuerySet().facet('bill_type', sort='index')\
                              .facet('sponsorships', sort='index')\
                              .facet('inferred_status')\
                              .facet('topics')\
                              .facet('legislative_session', sort='index')\
                              .highlight(**{'hl.fl': 'text,attachment_text'})

        data = None
        kwargs = {
            'load_all': self.load_all,
        }

        if form_kwargs:
            kwargs.update(form_kwargs)

        dataDict = {}
        if len(self.request.GET):
            data = self.request.GET
            dataDict = dict(data)

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = sqs

            if dataDict.get('sort_by'):
                for el in dataDict['sort_by']:
                    if el == 'date':
                        if dataDict.get('order_by') == ['asc']:
                            kwargs['searchqueryset'] = sqs.order_by('last_action_date')
                        else:
                            kwargs['searchqueryset'] = sqs.order_by('-last_action_date')
                    if el == 'title':
                        if dataDict.get('order_by') == ['desc']:
                            kwargs['searchqueryset'] = sqs.order_by('-sort_name')
                        else:
                            kwargs['searchqueryset'] = sqs.order_by('sort_name')
                    if el == 'relevance':
                        kwargs['searchqueryset'] = sqs

            elif dataDict.get('q'):
                kwargs['searchqueryset'] = sqs
            else:
                kwargs['searchqueryset'] = sqs.order_by('-last_action_date')

        return self.form_class(data, **kwargs)


class GoogleView(IndexView):
    template_name = 'lametro/google66b34bb6957ad66c.html'


class LAMetroArchiveSearch(TemplateView):
    template_name = 'lametro/archive_search.html'


def metro_login(request):
    logout(request)
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/events/')
    else:
        form = AuthenticationForm()
    return render(request, 'lametro/metro_login.html', {'form': form})


def metro_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

@csrf_exempt
def refresh_guid_trigger(request, refresh_key):
    try:
        if refresh_key == settings.REFRESH_KEY:
            management.call_command('refresh_guid')
            return HttpResponse(200)
        else:
            print('You do not have the correct refresh_key to access this.')
    except AttributeError:
        print('You need a refresh_key in your local deployment settings files to access this.')
    return HttpResponse(403)
