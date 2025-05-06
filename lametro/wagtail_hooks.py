from django import forms
from django.contrib import admin  # noqa
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q

import django_filters
from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
    PublishingPanel,
    HelpPanel,
)
from wagtail.admin.ui.tables import UpdatedAtColumn, LiveStatusTagColumn
from wagtail.documents.widgets import AdminDocumentChooser
from wagtail.permissions import ModelPermissionPolicy
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, CreateView

from lametro.services import EventService

from lametro.models import (
    Alert,
    BoardMemberDetails,
    LAMetroOrganization,
    EventNotice,
    FiscalYearCalendar,
    EventAgenda,
    LAMetroEvent,
    Tooltip,
)


class AlertFilterSet(django_filters.FilterSet):
    EXPIRED_CHOICES = (
        ("expired", "Expired"),
        ("all", "All Alerts"),
    )

    expired = django_filters.ChoiceFilter(
        label="Alert Status",
        method="filter_expired_alerts",
        choices=EXPIRED_CHOICES,
        empty_label="Not Expired",
    )

    def filter_expired_alerts(self, queryset, name, value):
        if value == "expired":
            return Alert.objects.filter(expiration__lte=timezone.now())
        elif value == "all":
            return Alert.objects.all()
        else:
            return queryset


class AlertViewSet(SnippetViewSet):
    model = Alert
    icon = "warning"
    menu_icon = "warning"
    menu_order = 100
    filterset_class = AlertFilterSet
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = ("content", "expiration")
    list_filter = ("type",)
    search_fields = (
        "type",
        "description",
    )

    def get_queryset(self, request):
        return Alert.objects.filter(
            Q(expiration__gt=timezone.now()) | Q(expiration__isnull=True)
        )


BOOLEAN_CHOICES = (
    ("true", "Yes"),
    ("false", "No"),
)


class NoAddModelPermissionPolicy(ModelPermissionPolicy):
    """
    Model permission that doesn't allow creating new instances.
    """

    def user_has_permission(self, user, action):
        if action in ("add", "delete"):
            return False
        return user.has_perm(self._get_permission_name(action))


class BoardMemberFilterSet(django_filters.FilterSet):
    current_member = django_filters.ChoiceFilter(
        label="Current member",
        choices=BOOLEAN_CHOICES,
        method="filter_current_member",
    )
    organization = django_filters.ModelChoiceFilter(
        label="Member of",
        queryset=LAMetroOrganization.objects.filter(memberships__isnull=False)
        .order_by("name")
        .distinct(),
        method="filter_organization",
    )

    def filter_current_member(self, queryset, name, value):
        people = [
            page.person
            for page in queryset.select_related("person")
            .prefetch_related("person__memberships")
            .distinct()
        ]

        if value == "true":
            filter_func = lambda person: person.current_memberships.exists()  # noqa
        else:
            filter_func = lambda person: not person.current_memberships.exists()  # noqa

        return queryset.filter(
            person__id__in=(p.id for p in filter(filter_func, people))
        )

    def filter_organization(self, queryset, name, value):
        return queryset.filter(person__memberships__organization=value).distinct()

    class Meta:
        model = BoardMemberDetails
        fields = ["current_member"]


class EventNoticeFilterSet(django_filters.FilterSet):
    broadcast_conditions = django_filters.ChoiceFilter(
        lookup_expr="icontains", choices=EventNotice.BROADCAST_CONDITION_CHOICES
    )
    comment_conditions = django_filters.ChoiceFilter(
        lookup_expr="icontains", choices=EventNotice.COMMENT_CONDITION_CHOICES
    )

    class Meta:
        model = EventNotice
        fields = ("broadcast_conditions", "comment_conditions")


class LinkedStatusTagColumn(LiveStatusTagColumn):
    cell_template_name = "snippets/related_object_status_tag.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sort_key = None

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["url"] = instance.get_url()
        return context


class BoardMemberDetailsViewSet(SnippetViewSet):
    model = BoardMemberDetails
    icon = "user"
    add_to_admin_menu = True
    menu_icon = "user"
    menu_order = 200
    filterset_class = BoardMemberFilterSet
    ordering = ("person__name",)
    search_fields = ("person__name",)
    list_display = [
        "__str__",
        UpdatedAtColumn(),
        LinkedStatusTagColumn(),
    ]

    @property
    def permission_policy(self):
        return NoAddModelPermissionPolicy(self.model)

    edit_handler = ObjectList(
        [
            HelpPanel(
                content=(
                    "<p>On this page, you can manage a board member's headshot and "
                    "bio. All other details and relationships, e.g., memberships, "
                    "should be managed in Legistar.</p>"
                    "<p><strong>Note:</strong> The page preview excludes "
                    "the map and committee and board report modules displayed "
                    "on the live page.</p>"
                )
            ),
            MultiFieldPanel(
                [
                    FieldPanel("headshot", heading="Image"),
                    FieldPanel("headshot_source", heading="Source"),
                ],
                heading="Headshot",
            ),
            FieldPanel("bio"),
            PublishingPanel(),
        ]
    )


class EventNoticeViewSet(SnippetViewSet):
    model = EventNotice
    icon = "comment"
    menu_icon = "comment"
    menu_order = 201
    filterset_class = EventNoticeFilterSet
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = (
        "get_message",
        "get_broadcast_conditions",
        "get_comment_conditions",
    )
    list_filter = (
        "broadcast_conditions",
        "comment_conditions",
    )
    search_fields = ("message",)


class FiscalYearCalendarViewSet(SnippetViewSet):
    model = FiscalYearCalendar
    base_url_path = "fiscal_year_calendar"
    menu_icon = "calendar-alt"
    menu_order = 202
    menu_label = "Fiscal Year Calendar"
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = (
        "title",
        "calendar",
    )


class EventAgendaForm(forms.ModelForm):
    class Meta:
        model = EventAgenda
        fields = ("event", "url", "document")
        widgets = {"document": AdminDocumentChooser}

    def __init__(self, *args, **kwargs):
        del kwargs["for_user"]

        super().__init__(*args, **kwargs)

        self.fields["event"].widget.choices = [
            (e.id, e) for e in LAMetroEvent.objects.all().order_by("start_date")
        ]


class EventAgendaCreateView(CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        if event := self.request.GET.get("event"):
            form_kwargs["instance"] = EventAgenda(
                event=LAMetroEvent.objects.get(slug=event)
            )
        return form_kwargs


class EventAgendaViewSet(SnippetViewSet):
    model = EventAgenda
    icon = "doc-full"
    add_to_admin_menu = True
    menu_icon = "doc-full"
    menu_order = 200
    list_display = [
        "__str__",
        UpdatedAtColumn(),
        LinkedStatusTagColumn(),
    ]
    ordering = ("-_updated_at",)
    add_view_class = EventAgendaCreateView

    def get_form_class(self, *args, **kwargs):
        return EventAgendaForm


class TooltipFilterSet(django_filters.FilterSet):
    DISABLED_CHOICES = (
        ("true", "Disabled"),
        ("all", "All Tooltips"),
    )

    disabled = django_filters.ChoiceFilter(
        label="Disabled",
        method="filter_disabled_tooltips",
        choices=DISABLED_CHOICES,
        empty_label="Not Disabled",
    )

    def filter_disabled_tooltips(self, queryset, name, value):
        if value == "true":
            return Tooltip.objects.filter(disabled=True)
        elif value == "all":
            return Tooltip.objects.all()
        else:
            return queryset


class TooltipViewSet(SnippetViewSet):
    model = Tooltip
    base_url_path = "tooltip"
    menu_icon = "info-circle"
    menu_order = 203
    filterset_class = TooltipFilterSet
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = ("target_label", "short_content", "is_disabled")
    list_filter = ("disabled",)
    search_fields = ("target_label", "content")

    def get_queryset(self, request):
        return Tooltip.objects.filter(disabled=False)


register_snippet(AlertViewSet)
register_snippet(EventNoticeViewSet)
register_snippet(FiscalYearCalendarViewSet)
register_snippet(BoardMemberDetailsViewSet)
register_snippet(EventAgendaViewSet)
register_snippet(TooltipViewSet)


class UserBarLink:
    icon_name = "edit"

    def get_icon(self):
        return format_html(
            """
            <svg class="icon icon-{0} w-action-icon" aria-hidden="true">
                <use href="#icon-{0}"></use>
            </svg>
            """.format(
                self.icon_name
            )
        )

    def render(self, request, href=None):
        if href is None:
            href = self.get_href(request)

        link_text = self.get_link_text(request)

        return format_html(
            """
            <li class="w-userbar__item" role="presentation">
                <a href="{0}" target="_parent" role="menuitem">
                    {1}
                    {2}
                </a>
            </li>
            """.format(
                href, self.get_icon(), link_text
            )
        )


class ViewSetLink(UserBarLink):
    icon_name = "plus"

    def __init__(self, viewset_cls):
        self.viewset = viewset_cls()

    def get_href(self, request):
        return f"/cms/{self.viewset.url_prefix}/"

    def get_link_text(self, request):
        return f"Manage {self.viewset.get_menu_label().lower()}"


class BoardMemberEditLink(UserBarLink):
    def render(self, request):
        if href := self.get_href(request):
            return super().render(request, href=href)

    def get_href(self, request):
        try:
            slug = request.resolver_match.kwargs["slug"]
        except KeyError:
            return

        try:
            snippet = BoardMemberDetails.objects.get(person__slug=slug)
        except BoardMemberDetails.DoesNotExist:
            return

        finder = AdminURLFinder()
        return finder.get_edit_url(snippet)

    def get_link_text(self, request):
        return "Edit this page"


class EventAgendaLink(UserBarLink):
    def render(self, request):
        if href := self.get_href(request):
            return super().render(request, href=href)

    def get_href(self, request):
        try:
            slug = request.resolver_match.kwargs["slug"]
        except KeyError:
            return

        event = LAMetroEvent.objects.get(slug=slug)

        if (
            not event.documents.exclude(note__icontains="manual")
            .filter(note__icontains="agenda")
            .exists()
        ):
            return EventService.get_manage_agenda_url(event)

    def get_link_text(self, request):
        return "Manage manual agenda"


@hooks.register("construct_wagtail_userbar")
def add_viewset_links(request, items):
    items.extend([BoardMemberEditLink(), EventAgendaLink()])
    for link in (AlertViewSet, EventNoticeViewSet, FiscalYearCalendarViewSet):
        items.append(ViewSetLink(link))
    return items


@hooks.register("insert_global_admin_js", order=500)
def insert_custom_wagtail_javascript():
    return format_html('<script src="{}"></script>', static("js/wagtail_custom.js"))


@hooks.register("insert_global_admin_css", order=500)
def insert_custom_wagtail_css():
    return format_html(
        '<link rel="stylesheet" href="{}"></script>', static("css/wagtail_custom.css")
    )
