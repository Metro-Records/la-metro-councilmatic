import itertools
import urllib
from datetime import datetime
from dateutil import parser
import requests
import logging

from haystack.query import SearchQuerySet

import pytz

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.db.models.functions import Lower, Now
from django.db.models import (
    Max,
    Prefetch,
    Case,
    When,
    Value,
    IntegerField,
    Q,
    F,
)
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    TemplateView,
    View,
)
from django.http import (
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    HttpResponseNotFound,
)
from django.core.serializers import serialize
from django.core.management import call_command
from django.core.cache import cache

from councilmatic_core.views import (
    IndexView,
    BillDetailView,
    CouncilMembersView,
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
    EventBroadcast,
    BoardMemberDetails,
)
from lametro.forms import (
    LAMetroCouncilmaticSearchForm,
)
from lametro.services import EventService
from lametro.exceptions import HerokuRequestError

from councilmatic.settings_jurisdiction import MEMBER_BIOS

from opencivicdata.legislative.models import EventDocument

from .utils import get_list_from_csv

app_timezone = pytz.timezone(settings.TIME_ZONE)
logger = logging.getLogger(__name__)


class LAMetroIndexView(IndexView):
    template_name = "index/index.html"

    event_model = LAMetroEvent

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["streaming_meetings"] = self.event_model._streaming_meeting()

        context["upcoming_board_meetings"] = self.event_model.upcoming_board_meetings()[
            :2
        ]
        context["most_recent_past_meetings"] = (
            self.event_model.most_recent_past_meetings()
        )
        context["current_meeting"] = self.event_model.current_meeting()
        context["bilingual"] = bool(
            [e for e in context["current_meeting"] if e.bilingual]
        )
        context["USING_ECOMMENT"] = settings.USING_ECOMMENT

        context["todays_meetings"] = self.event_model.todays_meetings().order_by(
            "start_date"
        )
        context["form"] = LAMetroCouncilmaticSearchForm()

        return context


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

    def get_queryset(self):
        # Get the queryset with prefetched media_urls in proper order.
        return LAMetroEvent.objects.with_media()

    def get_context_data(self, **kwargs) -> dict:
        context = super(EventDetailView, self).get_context_data(**kwargs)
        context["USING_ECOMMENT"] = settings.USING_ECOMMENT

        event = context["event"]

        if self.request.user.is_authenticated:
            context["legistar_ok"] = requests.head(
                "https://metro.legistar.com/calendar.aspx"
            ).ok
            context["event_ok"] = EventService.assert_consistent_with_api(event)

        context["minutes"] = EventService.get_minutes(event)
        context["related_board_reports"] = EventService.get_related_board_reports(event)
        context["agenda"] = EventService.get_agenda(event)
        context["manage_agenda_url"] = EventService.get_manage_agenda_url(event)
        context["notices"] = EventService.get_notices(event)

        return context


@login_required
def delete_event(request, event_slug):
    event = LAMetroEvent.objects.get(slug=event_slug)
    event.delete()
    return HttpResponseRedirect("/events/")


@login_required
def manual_event_live_link(request, event_slug):
    """
    Toggle a manually live event broadcast link
    """
    event = LAMetroEvent.objects.get(slug=event_slug)
    has_regular_broadcasts = event.broadcast.filter(is_manually_live=False).exists()
    manual_broadcasts = event.broadcast.filter(is_manually_live=True)

    if manual_broadcasts.count() == 0 and not has_regular_broadcasts:
        # Create a manual broadcast
        EventBroadcast.objects.create(event=event, is_manually_live=True)
        messages.success(request, f"Link for {event.name} has been manually published.")
    elif has_regular_broadcasts:
        messages.info(
            request,
            f"The event {event.name} already has a proper broadcast. "
            + "A manual broadcast cannot be created.",
        )
    else:
        # Delete that broadcast
        for b in manual_broadcasts:
            b.delete()
        messages.success(request, f"Link for {event.name} has been unpublished.")

    return HttpResponseRedirect(f"/event/{event_slug}")


class LAMetroEventsView(EventsView):
    template_name = "events/events.html"

    def get_context_data(self, **kwargs):
        context = {}

        def day_grouper(x):
            return datetime(
                x.local_start_time.year,
                x.local_start_time.month,
                x.local_start_time.day,
            ).date()

        # We only want to display approved minutes
        minutes_queryset = EventDocument.objects.filter(
            event__extras__approved_minutes=True, note__icontains="minutes"
        )

        # A base queryset for non-test objects with media
        media_events = LAMetroEvent.objects.with_media()

        # Did the user set date boundaries?
        start_date_str = self.request.GET.get("from")
        end_date_str = self.request.GET.get("to")

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

            org_select_events = itertools.groupby(select_events, key=day_grouper)
            context["select_events"] = [
                (d, list(events)) for d, events in org_select_events
            ]

        # Did user request all events?
        elif self.request.GET.get("show") == "all":
            all_events = media_events.order_by("-start_time")
            org_all_events = itertools.groupby(all_events, key=day_grouper)

            context["all_events"] = [(d, list(events)) for d, events in org_all_events]

        else:
            past_events = media_events.filter(start_time__lt=timezone.now()).order_by(
                "-start_time"
            )
            future_events = media_events.filter(start_time__gt=timezone.now()).order_by(
                "start_time"
            )

            # Limit past events shown unless user requested all
            if not self.request.GET.get("show") == "past":
                last_three_meeting_days = (
                    past_events.annotate(date=F("start_time__date"))
                    .order_by("-date")
                    .values_list("date", flat=True)
                    .distinct()[:3]
                )

                past_events = past_events.filter(
                    start_time__date__in=last_three_meeting_days
                ).order_by("-start_time")

            # Limit future events shown unless user requested all
            if not self.request.GET.get("show") == "future":
                next_three_meeting_days = (
                    future_events.annotate(date=F("start_time__date"))
                    .order_by("date")
                    .values_list("date", flat=True)
                    .distinct()[:3]
                )

                future_events = media_events.filter(
                    start_time__date__in=next_three_meeting_days
                ).order_by("start_time")

            # Prefetch documents for past events
            past_events = past_events.prefetch_related(
                Prefetch("documents", minutes_queryset, to_attr="minutes")
            ).prefetch_related("minutes__links")

            # Group meetings by day
            org_future_events = itertools.groupby(future_events, key=day_grouper)
            org_past_events = itertools.groupby(past_events, key=day_grouper)

            context["future_events"] = [
                (d, list(events)) for d, events in org_future_events
            ]
            context["past_events"] = [
                (d, list(events)) for d, events in org_past_events
            ]

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
            "map_geojson_caltrans": {"type": "FeatureCollection", "features": []},
        }

        posts = LAMetroPost.objects.filter(shape__isnull=False)

        for post in posts:
            for feature in post.geographic_features:
                if "council_district" in post.division_id:
                    maps["map_geojson_districts"]["features"].append(feature)

                if "la_metro_sector" in post.division_id:
                    maps["map_geojson_sectors"]["features"].append(feature)

                if (
                    post.division_id
                    == "ocd-division/country:us/state:ca/place:los_angeles"
                ):
                    maps["map_geojson_city"]["features"].append(feature)

                if "caltrans" in post.division_id:
                    maps["map_geojson_caltrans"]["features"].append(feature)

        if len(maps["map_geojson_caltrans"]) > 1:
            maps["map_geojson_caltrans"]["features"] = [
                f
                for f in maps["map_geojson_caltrans"]["features"]
                if f["properties"]["council_member"] != "Vacant"
            ]

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = context["person"]

        try:
            person_details = BoardMemberDetails.objects.get(person=person)
        except BoardMemberDetails.DoesNotExist:
            context["person_details"] = None
        else:
            context["person_details"] = (
                person_details.live_revision.as_object()
                if person_details.live_revision
                else None
            )

        council_post = (
            person.latest_council_membership.post
            if person.latest_council_membership
            else ""
        )

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


class LAMetroCouncilmaticFacetedSearchView(CouncilmaticFacetedSearchView):
    def __init__(self, *args, **kwargs):
        kwargs["form_class"] = LAMetroCouncilmaticSearchForm
        super(LAMetroCouncilmaticFacetedSearchView, self).__init__(*args, **kwargs)
        self.load_all = False

    def extra_context(self):
        # Raise an error if Councilmatic cannot connect to the search engine.
        # Most likely, the search engine is down and needs restarting.
        try:
            search_engine_url = settings.HAYSTACK_CONNECTIONS["default"]["URL"]
            requests.get(search_engine_url)
        except requests.ConnectionError:
            raise Exception(
                "ConnectionError: Unable to connect to the searchg engine at {}. Is the search engine running?".format(
                    search_engine_url
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
                try:
                    [k, v] = val.split("_exact:", 1)
                except ValueError:
                    continue

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
                            kwargs["searchqueryset"] = sqs.order_by(
                                "last_action_date", "-_score"
                            )
                        else:
                            kwargs["searchqueryset"] = sqs.order_by(
                                "-last_action_date", "-_score"
                            )
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


class TagAnalyticsView(LoginRequiredMixin, View):
    login_url = "/cms/"

    def get(self, request):
        try:
            success_url = request.META["HTTP_REFERER"]
        except KeyError:
            # Prevent users from starting the job when pasting a link
            messages.error(
                request,
                "To generate new analytics, please use either the "
                "link in the Reports section of the CMS, or in the Wagtail user bar.",
            )
            return HttpResponseRedirect(request.build_absolute_uri("/cms/"))

        if not settings.HEROKU_APP_NAME:
            # Run cmd as is, and save analytics locally
            call_command("generate_tag_analytics", "--local")
            messages.success(request, "Google tag analytics generated!")
            return HttpResponseRedirect(success_url)

        url = f"https://api.heroku.com/apps/{settings.HEROKU_APP_NAME}/dynos"
        headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {settings.HEROKU_KEY}",
        }

        if worker_id := cache.get("worker_id"):
            # Check if that worker is still running the cmd
            response = requests.get(url + f"/{worker_id}", headers=headers)
            try:
                worker_state = response.json().get("state")
            except requests.exceptions.JSONDecodeError:
                messages.error(
                    request,
                    f"Received a {response.status_code} status code from Heroku. "
                    "Cannot check status of recent analytics job. "
                    "Administrators have been notified.",
                )
                raise HerokuRequestError(response=response)

            if worker_state in ["starting", "up"]:
                messages.info(
                    request,
                    "The analytics you requested earlier are still processing. "
                    "You can request another once that job is finished.",
                )
                return HttpResponseRedirect(success_url)
            else:
                # Old worker done. Clear out the id so we can start a new one.
                cache.delete("worker_id")

        # Send the task to a background worker
        # For Heroku Platform dyno creation API reference, see:
        # https://devcenter.heroku.com/articles/platform-api-reference#dyno-create
        email = request.user.email
        command = f"python manage.py generate_tag_analytics --email {email}"
        data = {
            "command": command,
            "attach": False,  # Start a detached (daemon) dyno
            "type": "run",
        }

        logger.info(f"Sending command to Heroku: {command}")
        response = requests.post(url, json=data, headers=headers)
        logger.info(
            f"Got {response.status_code} response from Heroku: {response.json()}"
        )

        try:
            response.raise_for_status()
            cache.set("worker_id", response.json()["name"], 3600)
        except requests.exceptions.HTTPError:
            messages.error(
                request,
                f"Received a {response.status_code} status code from Heroku. "
                "Analytics not generated, and administrators have been notified.",
            )
            raise HerokuRequestError(response=response)
        else:
            messages.info(
                request,
                "Tag analytics are being generated! This will take several "
                "minutes. You will receive a link in your email when done.",
            )

        return HttpResponseRedirect(success_url)


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
