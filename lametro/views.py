import re
from operator import attrgetter
import itertools
import urllib
import json
from datetime import date, datetime
from dateutil import parser
import requests
import os

from haystack.backends.solr_backend import SolrSearchQuery
from haystack.query import SearchQuerySet

import pytz

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.db.models.functions import Lower, Now, Cast
from django.db.models import Max, Prefetch, Case, When, Value, IntegerField, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView
from django.http import (
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    HttpResponseNotFound,
)
from django.core import management
from django.core.serializers import serialize
from django.core.cache import cache

from councilmatic_core.views import (
    IndexView,
    BillDetailView,
    CouncilMembersView,
    AboutView,
    CommitteeDetailView,
    CommitteesView,
    PersonDetailView,
    EventDetailView,
    EventsView,
    CouncilmaticFacetedSearchView,
)
from councilmatic_core.models import Organization, Membership

from opencivicdata.core.models import PersonLink

from lametro.models import (
    LAMetroBill,
    LAMetroPost,
    LAMetroPerson,
    LAMetroEvent,
    LAMetroOrganization,
    LAMetroSubject,
)
from lametro.forms import (
    AgendaUrlForm,
    AgendaPdfForm,
    LAMetroCouncilmaticSearchForm,
    PersonHeadshotForm,
    PersonBioForm,
)

from councilmatic.settings_jurisdiction import MEMBER_BIOS, BILL_STATUS_DESCRIPTIONS
from councilmatic.settings import PIC_BASE_URL
from councilmatic.custom_storage import MediaStorage

from opencivicdata.legislative.models import EventDocument

from .utils import get_list_from_csv

app_timezone = pytz.timezone(settings.TIME_ZONE)


class LAMetroIndexView(IndexView):
    template_name = "index/index.html"

    event_model = LAMetroEvent

    @property
    def extra_context(self):
        extra = {}

        extra["upcoming_board_meetings"] = self.event_model.upcoming_board_meetings()[
            :2
        ]
        extra[
            "most_recent_past_meetings"
        ] = self.event_model.most_recent_past_meetings()
        extra["current_meeting"] = self.event_model.current_meeting()
        extra["bilingual"] = bool([e for e in extra["current_meeting"] if e.bilingual])
        extra["USING_ECOMMENT"] = settings.USING_ECOMMENT

        extra["todays_meetings"] = self.event_model.todays_meetings().order_by(
            "start_date"
        )
        extra["form"] = LAMetroCouncilmaticSearchForm()

        return extra


class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = "legislation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill = self.get_object()

        context["attachments"] = bill.attachments.all().order_by(Lower("note"))

        actions = bill.actions.all()
        organization_lst = [action.organization for action in actions]
        context["sponsorships"] = set(organization_lst)

        related_bills = (
            context["legislation"]
            .related_bills.exclude(related_bill__isnull=True)
            .annotate(latest_date=Max("related_bill__actions__date"))
            .order_by("-latest_date")
        )

        context["related_bills"] = related_bills

        context["actions"] = bill.actions_and_agendas

        return context


class LAMetroEventDetail(EventDetailView):
    model = LAMetroEvent
    template_name = "event/event.html"

    def post(self, request, *args, **kwargs):
        # Assign object to detail view, so that get_context_data can find this
        # variable: https://stackoverflow.com/questions/34460708/checkoutview-object-has-no-attribute-object
        self.object = self.get_object()
        event = self.get_object()
        event_slug = event.slug

        # Look for the button name and assign form values.
        if "url_form" in request.POST:
            url_form = AgendaUrlForm(request.POST)
            pdf_form = AgendaPdfForm()
        elif "pdf_form" in request.POST:
            pdf_form = AgendaPdfForm(request.POST, request.FILES)
            url_form = AgendaUrlForm()

        # Validate forms and redirect.
        if url_form.is_valid():
            agenda_url = url_form["agenda"].value()
            document_obj, created = EventDocument.objects.get_or_create(
                event=event, note="Event Document - Manual upload URL"
            )

            document_obj.date = timezone.now().date()
            document_obj.save()

            document_obj.links.create(url=agenda_url)

            return HttpResponseRedirect("/event/%s" % event_slug)
        elif pdf_form.is_valid() and "pdf_form" in request.POST:
            agenda_pdf = request.FILES["agenda"]

            handle_uploaded_agenda(agenda=agenda_pdf, event=event)

            return HttpResponseRedirect("/event/%s" % event_slug)
        else:
            return self.render_to_response(
                self.get_context_data(url_form=url_form, pdf_form=pdf_form)
            )

    def get_queryset(self):
        # Get the queryset with prefetched media_urls in proper order.
        return LAMetroEvent.objects.with_media()

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        event = context["event"]

        # Metro admins should see a status report if Legistar is down.
        # GET the calendar page, which contains relevant URL for agendas.
        if self.request.user.is_authenticated:
            r = requests.get("https://metro.legistar.com/calendar.aspx")
            context["legistar_ok"] = r.ok

            # GET the event URL; allow admin to delete event if 404
            # or if event name has changed
            # https://github.com/datamade/la-metro-councilmatic/issues/692#issuecomment-934648716
            api_rep = event.api_representation

            if api_rep:
                context["event_ok"] = event.api_body_name == api_rep["EventBodyName"]
            else:
                context["event_ok"] = False

        try:
            context["minutes"] = event.documents.get(note__icontains="minutes")
        except EventDocument.DoesNotExist:
            pass

        agenda_with_board_reports = (
            event.agenda.filter(related_entities__bill__versions__isnull=False)
            .annotate(int_order=Cast("order", IntegerField()))
            .order_by("int_order")
        )

        # Find agenda link.
        if event.documents.all():
            for document in event.documents.all():
                if "Agenda" in document.note:
                    context["agenda_url"] = document.links.first().url
                    context["document_timestamp"] = document.date
                elif "Manual upload URL" in document.note:
                    context["uploaded_agenda_url"] = document.links.first().url
                    context["document_timestamp"] = document.date
                elif "Manual upload PDF" in document.note:
                    context["uploaded_agenda_pdf"] = document.links.first().url
                    context["document_timestamp"] = document.date
                    """
                    LA Metro Councilmatic uses the adv_cache library
                    to partially cache templates: in the event view, we cache
                    the entire template, except the iframe. (N.B. With
                    this library, the views do not cached, unless
                    explicitly wrapped in a django cache decorator.
                    Nonetheless, several popular browsers (e.g.,
                    Chrome and Firefox) retrieve cached iframe images,
                    regardless of the site's caching specifications.
                    We use the agenda's "date" timestamp to bust
                    the iframe cache: we save it inside context and
                    then assign it as the "name" of the iframe,
                    preventing the browser from retrieving a cached
                    iframe, when the timestamp changes.
                    """

        context["related_board_reports"] = agenda_with_board_reports
        context["base_url"] = PIC_BASE_URL  # Give JS access to this variable

        context["has_agenda"] = (
            context.get("agenda_url")
            or context.get("uploaded_agenda_url")
            or context.get("uploaded_agenda_pdf")
        )

        # Render forms if not a POST request
        if "url_form" not in context:
            context["url_form"] = AgendaUrlForm()
        if "pdf_form" not in context:
            context["pdf_form"] = AgendaPdfForm()

        context["USING_ECOMMENT"] = settings.USING_ECOMMENT

        return context


def handle_uploaded_agenda(agenda, event):
    with open("lametro/static/pdf/agenda-%s.pdf" % event.slug, "wb+") as destination:
        for chunk in agenda.chunks():
            destination.write(chunk)

    # Create the document in database
    document_obj, created = EventDocument.objects.get_or_create(
        event=event, note="Event Document - Manual upload PDF"
    )

    document_obj.date = timezone.now().date()
    document_obj.links.create(url="pdf/agenda-%s.pdf" % event.slug)
    document_obj.save()

    # Collect static to render PDF on server
    management.call_command("collectstatic", "--noinput")


@login_required
def delete_submission(request, event_slug):
    event = LAMetroEvent.objects.get(slug=event_slug)
    event_doc = EventDocument.objects.filter(
        event_id=event.id, note__icontains="Manual upload"
    )

    for e in event_doc:
        # Remove stored PDF from Metro app.
        if "Manual upload PDF" in e.note:
            try:
                os.remove("lametro/static/%s" % e.links.get().url)
            except OSError:
                pass
        e.delete()

    return HttpResponseRedirect("/event/%s" % event_slug)


@login_required
def delete_event(request, event_slug):
    event = LAMetroEvent.objects.get(slug=event_slug)
    event.delete()
    return HttpResponseRedirect("/events/")


class LAMetroEventsView(EventsView):
    template_name = "events/events.html"

    def get_context_data(self, **kwargs):
        context = {}

        # Did the user set date boundaries?
        start_date_str = self.request.GET.get("from")
        end_date_str = self.request.GET.get("to")

        def day_grouper(x):
            return (
                x.local_start_time.year,
                x.local_start_time.month,
                x.local_start_time.day,
            )

        # We only want to display approved minutes
        minutes_queryset = EventDocument.objects.filter(
            event__extras__approved_minutes=True, note__icontains="minutes"
        )

        # A base queryset for non-test objects with media
        media_events = LAMetroEvent.objects.with_media().exclude(name__icontains="test")

        # If yes...
        if start_date_str and end_date_str:
            context["start_date"] = start_date_str
            context["end_date"] = end_date_str
            start_date_time = parser.parse(start_date_str)
            end_date_time = parser.parse(end_date_str)

            select_events = (
                media_events.filter(start_time__gt=start_date_time)
                .filter(start_time__lt=end_date_time)
                .order_by("start_time")
            )
            select_events = select_events.prefetch_related(
                Prefetch("documents", minutes_queryset, to_attr="minutes")
            ).prefetch_related("minutes__links")

            org_select_events = []

            for event_date, events in itertools.groupby(select_events, key=day_grouper):
                events = sorted(events, key=attrgetter("start_time"))
                org_select_events.append([date(*event_date), events])

            context["select_events"] = org_select_events

        # If all meetings
        elif self.request.GET.get("show"):
            all_events = media_events.order_by("-start_time")
            org_all_events = []

            for event_date, events in itertools.groupby(all_events, key=day_grouper):
                events = sorted(events, key=attrgetter("start_time"))
                org_all_events.append([date(*event_date), events])

            context["all_events"] = org_all_events
        # If no...
        else:
            # Upcoming events
            future_events = media_events.filter(start_time__gt=timezone.now()).order_by(
                "start_time"
            )
            org_future_events = []

            for event_date, events in itertools.groupby(future_events, key=day_grouper):
                events = sorted(events, key=attrgetter("start_time"))
                org_future_events.append([date(*event_date), events])

            context["future_events"] = org_future_events

            # Past events
            past_events = media_events.filter(start_time__lt=timezone.now()).order_by(
                "-start_time"
            )

            past_events = past_events.prefetch_related(
                Prefetch("documents", minutes_queryset, to_attr="minutes")
            ).prefetch_related("minutes__links")

            org_past_events = []

            for event_date, events in itertools.groupby(past_events, key=day_grouper):
                events = sorted(events, key=attrgetter("start_time"))
                org_past_events.append([date(*event_date), events])

            context["past_events"] = org_past_events

        context["user_subscribed"] = False
        if self.request.user.is_authenticated:
            user = self.request.user
            context["user"] = user

            if settings.USING_NOTIFICATIONS:
                if len(user.eventssubscriptions.all()) > 0:
                    context["user_subscribed"] = True

        return context


class LABoardMembersView(CouncilMembersView):
    template_name = "board_members/board_members.html"

    def map(self):
        maps = {
            "map_geojson_districts": {"type": "FeatureCollection", "features": []},
            "map_geojson_sectors": {"type": "FeatureCollection", "features": []},
            "map_geojson_city": {"type": "FeatureCollection", "features": []},
        }

        posts = LAMetroPost.objects.filter(shape__isnull=False).exclude(
            label="Appointee of Mayor of the City of Los Angeles"
        )

        for post in posts:
            district = post.label

            try:
                current_membership = post.memberships.get(
                    start_date_dt__lte=Now(), end_date_dt__gt=Now()
                )

            except ObjectDoesNotExist:
                council_member = "Vacant"
                detail_link = ""

            else:
                council_member = current_membership.person.name
                detail_link = current_membership.person.slug

            feature = {
                "type": "Feature",
                "geometry": json.loads(post.shape.json),
                "properties": {
                    "district": district,
                    "council_member": council_member,
                    "detail_link": "/person/" + detail_link,
                    "select_id": "polygon-{}".format(slugify(district)),
                },
            }

            if "council_district" in post.division_id:
                maps["map_geojson_districts"]["features"].append(feature)

            if "la_metro_sector" in post.division_id:
                maps["map_geojson_sectors"]["features"].append(feature)

            if post.division_id == "ocd-division/country:us/state:ca/place:los_angeles":
                maps["map_geojson_city"]["features"].append(feature)

        return maps

    def get_queryset(self):
        board = Organization.objects.get(name=settings.OCD_CITY_COUNCIL_NAME)

        memberships = board.memberships.filter(
            Q(role="Board Member") | Q(role="Nonvoting Board Member")
        ).filter(start_date_dt__lt=Now(), end_date_dt__gte=Now())

        display_order = {
            "Chair": 0,
            "Vice Chair": 1,
            "1st Chair": 1,
            "1st Vice Chair": 1,
            "2nd Chair": 2,
            "2nd Vice Chair": 2,
            "Board Member": 3,
            "Nonvoting Board Member": 4,
        }

        sortable_memberships = []

        # Display board leadership first. Person.board_office is null for
        # members without leadership roles, so fall back to using their
        # board membership role to decide display order.
        for m in memberships:
            primary_post = m.person.board_office or m
            m.index = display_order[primary_post.role]
            sortable_memberships.append(m)

        return sorted(
            sortable_memberships, key=lambda x: (x.index, x.person.family_name)
        )

    def get_context_data(self, *args, **kwargs):
        context = super(CouncilMembersView, self).get_context_data(**kwargs)

        context["seo"] = self.get_seo_blob()

        board = LAMetroOrganization.objects.get(name=settings.OCD_CITY_COUNCIL_NAME)
        context["recent_activity"] = board.actions.order_by(
            "-date", "-bill__identifier", "-order"
        )
        context["recent_events"] = board.recent_events

        if settings.MAP_CONFIG:
            context.update(self.map())

        return context


class LAMetroAboutView(AboutView):
    template_name = "about/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["timestamp"] = datetime.now(app_timezone).strftime("%m%d%Y%s")

        context["BILL_STATUS_DESCRIPTIONS"] = BILL_STATUS_DESCRIPTIONS

        return context


class LACommitteesView(CommitteesView):
    template_name = "committees.html"

    def get_queryset(self):
        """
        We only want committees that have at least one current member who is not
        the CEO. We also want to not count the CEO in the committee
        size.
        """
        ceo = LAMetroPerson.ceo()

        memberships = Membership.objects.exclude(person=ceo).filter(
            start_date_dt__lte=Now(),
            end_date_dt__gt=Now(),
            organization__classification="committee",
        )

        qs = (
            LAMetroOrganization.objects.filter(classification="committee")
            .filter(memberships__in=memberships)
            .distinct()
        )

        qs = qs.prefetch_related(
            Prefetch("memberships", memberships, to_attr="current_members")
        )

        return qs


class LACommitteeDetailView(CommitteeDetailView):
    model = LAMetroOrganization
    template_name = "committee.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        committee = context["committee"]

        if getattr(settings, "COMMITTEE_DESCRIPTIONS", None):
            description = settings.COMMITTEE_DESCRIPTIONS.get(committee.slug)
            context["committee_description"] = description

        ceo = LAMetroPerson.ceo()

        non_ceos = (
            committee.all_members.annotate(
                index=Case(
                    When(role="Chair", then=Value(0)),
                    When(role="Vice Chair", then=Value(1)),
                    When(role="1st Vice Chair", then=Value(1)),
                    When(role="2nd Vice Chair", then=Value(2)),
                    When(role="Member", then=Value(3)),
                    default=Value(999),
                    output_field=IntegerField(),
                )
            )
            .exclude(person=ceo)
            .order_by("index", "person__family_name", "person__given_name")
        )

        context["non_ceos"] = non_ceos

        context["ceo"] = ceo

        return context


class LAPersonDetailView(PersonDetailView):
    template_name = "person/person.html"
    model = LAMetroPerson

    def dispatch(self, request, *args, **kwargs):
        slug = self.kwargs["slug"]

        try:
            person = self.model.objects.get(slug=slug)

        except LAMetroPerson.DoesNotExist:
            person = None

        else:
            response = super().dispatch(request, *args, **kwargs)

        if not person:
            # Grab the first and last name from slug like "john-smith-af5a8ab39aad"
            short_slug = "-".join(slug.split("-")[:-1])

            try:
                person = self.model.objects.get(slug__startswith=short_slug)
            except (LAMetroPerson.DoesNotExist, LAMetroPerson.MultipleObjectsReturned):
                # Return a 404 if more than one matching slug, or if there are no matching slugs
                response = HttpResponseNotFound()
            else:
                response = HttpResponsePermanentRedirect(
                    reverse("person", args=[person.slug])
                )

        return response

    def post(self, request, *args, **kwargs):
        slug = self.kwargs["slug"]
        person = self.model.objects.get(slug=slug)
        self.object = self.get_object()

        # The submitted hidden field determines which form was used
        if "bio_form" in request.POST:
            form = PersonBioForm(request.POST, instance=person)
            bio_content = request.POST.get("councilmatic_biography")

            # Prevent whitespace from being submitted
            if bio_content.isspace():
                error = "Please fill out the bio"
                return self.render_to_response(
                    self.get_context_data(form=form, bio_error=error)
                )
            else:
                form.save()
                return HttpResponseRedirect(self.request.path_info)

        elif "headshot_form" in request.POST:
            form = PersonHeadshotForm(request.POST, instance=person)
            file_obj = request.FILES.get("headshot", "")

            is_valid_file = self.validate_file(file_obj)

            if not is_valid_file:
                error = "Must be a valid image file, and size must be under 7.5mb."
                return self.render_to_response(
                    self.get_context_data(form=form, headshot_error=error)
                )

            person.headshot = self.get_file_url(request, file_obj)
            person.save()

            cache.clear()

            return HttpResponseRedirect(self.request.path_info)

    def validate_file(self, file):
        image_formats = (".png", ".jpeg", ".jpg", ".tif", ".tiff", ".webp", ".avif")

        is_image = file.name.endswith(tuple(image_formats))
        max_file_size = 7864320  # 7.5mb

        if is_image and file.size <= max_file_size:
            return True
        return False

    def get_file_url(self, request, file):
        # Save file in bucket and return the resulting url

        file_dir_within_bucket = "user_upload_files/{username}".format(
            username=request.user
        )

        # create full file path
        file_path_within_bucket = os.path.join(file_dir_within_bucket, file.name)

        media_storage = MediaStorage()

        media_storage.save(file_path_within_bucket, file)
        file_url = media_storage.url(file_path_within_bucket)
        return file_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = context["person"]

        context["headshot_form"] = PersonHeadshotForm
        context["biography_form"] = PersonBioForm

        council_post = person.latest_council_membership.post

        try:
            context["qualifying_post"] = council_post.acting_label
        except AttributeError:
            context["qualifying_post"] = None

        try:
            if council_post.shape:
                context["map_geojson"] = serialize(
                    "geojson", [council_post], geometry_field="shape", fields=()
                )
            else:
                context["map_geojson"] = None
        except AttributeError:
            context["map_geojson"] = None

        if person.committee_sponsorships:
            context["sponsored_legislation"] = person.committee_sponsorships
        else:
            context["sponsored_legislation"] = []

        context["memberships_list"] = (
            person.current_memberships.exclude(organization__name="Board of Directors")
            .annotate(
                index=Case(
                    When(role="Chair", then=Value(0)),
                    When(role="Vice Chair", then=Value(1)),
                    When(role="1st Vice Chair", then=Value(1)),
                    When(role="2nd Vice Chair", then=Value(2)),
                    When(role="Member", then=Value(3)),
                    default=Value(999),
                    output_field=IntegerField(),
                )
            )
            .order_by("index")
        )

        if person.slug_name in MEMBER_BIOS:
            context["member_bio"] = MEMBER_BIOS[person.slug_name]

        try:
            context["website_url"] = person.links.get(note="web_site").url
        except PersonLink.DoesNotExist:
            pass

        return context


class IdentifierBoostSearchQuery(SolrSearchQuery):
    def run(self, spelling_query=None, **kwargs):
        """
        If the search contains identifiers, boost results with matching
        identifiers.

        Reference:
        https://medium.com/@pablocastelnovo/if-they-match-i-want-them-to-be-always-first-boosting-documents-in-apache-solr-with-the-boost-362abd36476c
        """
        # Remove slashes escaping the dash in an identifier
        identifiers = set(
            i.replace("\\", "")
            for i in re.findall(r"\d{4}\\-\d{4}", self.build_query())
        )

        if identifiers:
            kwargs.update(
                {
                    "defType": "edismax",
                    "bq": "+".join(
                        'identifier:"{}"^2.0'.format(i) for i in identifiers
                    ),
                }
            )

        return super().run(spelling_query, **kwargs)


class LAMetroCouncilmaticFacetedSearchView(CouncilmaticFacetedSearchView):
    load_all = False

    def __init__(self, *args, **kwargs):
        kwargs["form_class"] = LAMetroCouncilmaticSearchForm
        super(LAMetroCouncilmaticFacetedSearchView, self).__init__(*args, **kwargs)

    def extra_context(self):
        # Raise an error if Councilmatic cannot connect to Solr.
        # Most likely, Solr is down and needs restarting.
        try:
            solr_url = settings.HAYSTACK_CONNECTIONS["default"]["URL"]
            requests.get(solr_url)
        except requests.ConnectionError:
            raise Exception(
                "ConnectionError: Unable to connect to Solr at {}. Is Solr running?".format(
                    solr_url
                )
            )

        extra_context = {}
        extra_context.update(self.get_search_context())

        return extra_context

    def get_search_context(self):
        q_filters = ""

        url_params = [
            (p, val)
            for p, val in self.request.GET.items()
            if p not in ("page", "selected_facets", "amp", "_")
        ]

        search_term = self.request.GET.get("q")

        for facet_val in self.request.GET.getlist("selected_facets"):
            url_params.append(("selected_facets", facet_val))

        if url_params:
            q_filters = urllib.parse.urlencode(url_params)

        selected_facets = {}

        for val in self.request.GET.getlist("selected_facets"):
            if val:
                [k, v] = val.split("_exact:", 1)
                try:
                    selected_facets[k].append(v)
                except KeyError:
                    selected_facets[k] = [v]

        topic_facets = [facet for facet, _ in LAMetroSubject.CLASSIFICATION_CHOICES]

        return {
            "search_term": search_term,
            "facets": self.results.facet_counts(),
            "topic_facets": topic_facets,
            "selected_facets": selected_facets,
            "q_filters": q_filters,
        }

    def build_form(self, form_kwargs=None):
        if not form_kwargs:
            form_kwargs = {}

        form_kwargs["selected_facets"] = self.request.GET.getlist("selected_facets")
        form_kwargs["search_corpus"] = (
            "bills" if self.request.GET.get("search-reports") else "all"
        )
        form_kwargs["result_type"] = self.request.GET.get("result_type", "all")

        sqs = (
            SearchQuerySet()
            .facet("bill_type")
            .facet("sponsorships")
            .facet("legislative_session")
            .facet("inferred_status")
            .facet("topics")
            .facet("lines_and_ways")
            .facet("phase")
            .facet("project")
            .facet("metro_location")
            .facet("geo_admin_location")
            .facet("motion_by")
            .facet("significant_date")
            .facet("plan_program_policy")
        )

        data = None
        kwargs = {
            "load_all": self.load_all,
        }

        if form_kwargs:
            kwargs.update(form_kwargs)

        dataDict = {}
        if len(self.request.GET):
            data = self.request.GET
            dataDict = dict(data)

        if self.searchqueryset is not None:
            kwargs["searchqueryset"] = sqs

            if dataDict.get("sort_by"):
                for el in dataDict["sort_by"]:
                    if el == "date":
                        if dataDict.get("order_by") == ["asc"]:
                            kwargs["searchqueryset"] = sqs.order_by("last_action_date")
                        else:
                            kwargs["searchqueryset"] = sqs.order_by("-last_action_date")
                    if el == "title":
                        if dataDict.get("order_by") == ["desc"]:
                            kwargs["searchqueryset"] = sqs.order_by("-sort_name")
                        else:
                            kwargs["searchqueryset"] = sqs.order_by("sort_name")
                    if el == "relevance":
                        kwargs["searchqueryset"] = sqs

            elif dataDict.get("q"):
                kwargs["searchqueryset"] = sqs
            else:
                kwargs["searchqueryset"] = sqs.order_by("-last_action_date")

        return self.form_class(data, **kwargs)


class GoogleView(IndexView):
    template_name = "google66b34bb6957ad66c.html"


class LAMetroArchiveSearch(TemplateView):
    template_name = "archive_search.html"


class LAMetroContactView(IndexView):
    template_name = "contact.html"


class MinutesView(EventsView):
    template_name = "minutes/minutes.html"

    def _get_historical_events(self, start_datetime=None, end_datetime=None):
        csv_events = get_list_from_csv("historical_events.csv")

        filtered_historical_events = []
        if start_datetime or end_datetime:
            for e in csv_events:
                e_datetime = datetime.strptime(e["date"], "%Y-%m-%d")
                if start_datetime and end_datetime:
                    if e_datetime >= start_datetime and e_datetime <= end_datetime:
                        filtered_historical_events.append(e)
                elif start_datetime:
                    if e_datetime >= start_datetime:
                        filtered_historical_events.append(e)
                elif end_datetime:
                    if e_datetime <= end_datetime:
                        filtered_historical_events.append(e)
        else:
            filtered_historical_events = csv_events

        for obj in filtered_historical_events:
            obj["start_time"] = timezone.make_aware(
                datetime.strptime(obj["date"], "%Y-%m-%d")
            ).date()
            obj["agenda_link"] = obj["agenda_link"].split("\n")
            obj["minutes_link"] = obj["minutes_link"].split("\n")

        return filtered_historical_events

    def _get_stored_events(self, start_datetime=None, end_datetime=None):
        # we only want to display meetings that can have minutes
        meetings_with_minutes = (
            Q(event__name__icontains="LA SAFE")
            | Q(event__name__icontains="Board Meeting")
            | Q(event__name__icontains="Crenshaw Project Corporation")
        )

        minutes = EventDocument.objects.filter(
            meetings_with_minutes, note__icontains="minutes"
        ).prefetch_related(Prefetch("links", to_attr="prefetched_links"))

        agenda = EventDocument.objects.filter(
            meetings_with_minutes, note__icontains="agenda"
        ).prefetch_related(Prefetch("links", to_attr="prefetched_links"))

        all_events = (
            LAMetroEvent.objects.filter(meetings_with_minutes)
            .prefetch_related(
                Prefetch("documents", queryset=minutes, to_attr="minutes_document")
            )
            .prefetch_related(
                Prefetch("documents", queryset=agenda, to_attr="agenda_document")
            )
        )

        if start_datetime:
            stored_events = all_events.filter(start_time__gt=start_datetime)
        else:
            stored_events = all_events
        if end_datetime:
            stored_events = stored_events.filter(start_time__lt=end_datetime)
        else:
            stored_events = stored_events.filter(start_time__lt=timezone.now())

        structured_db_events = []
        for event in stored_events:
            stored_events_dict = {
                "start_time": event.start_time.date(),
                "meeting": event.name,
                "minutes_link": [],
                "agenda_link": [],
            }
            try:
                minutes_link = event.minutes_document[0].prefetched_links[0].url
                stored_events_dict["minutes_link"].append(minutes_link)
            except IndexError:
                pass

            try:
                agenda_link = event.agenda_document[0].prefetched_links[0].url
                stored_events_dict["agenda_link"].append(agenda_link)
            except IndexError:
                pass

            structured_db_events.append(stored_events_dict)

        return structured_db_events

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        start_datetime = None
        end_datetime = None

        start_date_str = self.request.GET.get("minutes-from", "")
        if start_date_str:
            start_datetime = datetime.strptime(start_date_str, "%m/%d/%Y")

        end_date_str = self.request.GET.get("minutes-to", "")
        if end_date_str:
            end_datetime = datetime.strptime(end_date_str, "%m/%d/%Y")

        context["start_date"] = start_date_str
        context["end_date"] = end_date_str

        historical_events = self._get_historical_events(start_datetime, end_datetime)
        stored_events = self._get_stored_events(start_datetime, end_datetime)

        # sort and group csv and db events together
        all_minutes = historical_events + stored_events
        all_minutes_sorted = sorted(
            all_minutes, key=lambda x: x["start_time"], reverse=True
        )

        all_minutes_grouped = []
        for event_date, events in itertools.groupby(
            all_minutes_sorted, key=lambda x: x["start_time"]
        ):
            events = sorted(events, key=lambda x: x["start_time"])
            all_minutes_grouped.append([event_date, events])

        context["all_minutes"] = all_minutes_grouped

        return context


def metro_login(request):
    logout(request)
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return HttpResponseRedirect("/events/")
    else:
        form = AuthenticationForm()
    return render(request, "metro_login.html", {"form": form})


def metro_logout(request):
    logout(request)
    return HttpResponseRedirect("/")


def pong(request):
    from django.http import HttpResponse

    try:
        from .deployment import DEPLOYMENT_ID
    except ImportError as e:
        return HttpResponse(f"Bad deployment: {e}", status=401)

    return HttpResponse(DEPLOYMENT_ID)


def test_logging(request):
    raise ValueError("Testing logging...")
