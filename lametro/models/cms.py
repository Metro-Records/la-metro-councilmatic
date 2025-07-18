from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import URLValidator
from django.db import models
from django.urls import reverse
from django import forms
from django.utils.html import format_html, strip_tags
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from html import unescape

from wagtail.documents import get_document_model
from wagtail.models import Page, PreviewableMixin, DraftStateMixin, RevisionMixin
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.rich_text import expand_db_html

from lametro.blocks import ArticleBlock, AsideBlock


class AboutPage(Page):
    include_in_dump = True

    body = StreamField(
        [
            ("section", ArticleBlock()),
        ],
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]


class BoardPoliciesPage(Page):
    include_in_dump = True

    body = StreamField(
        [
            ("section", ArticleBlock()),
            ("aside", AsideBlock()),
        ],
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    def get_sections(self):
        sections = [b for b in self.body if b.block_type == "section"]
        return sections

    def get_asides(self):
        asides = [b for b in self.body if b.block_type == "aside"]
        return asides


class BoardMemberDetails(
    DraftStateMixin, RevisionMixin, PreviewableMixin, models.Model
):
    include_in_dump = True

    class Meta:
        verbose_name_plural = "Board Member Details"

    person = models.OneToOneField(
        "lametro.LAMetroPerson", on_delete=models.CASCADE, related_name="details"
    )
    headshot = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    headshot_source = models.CharField(
        max_length=256, blank=True, null=True, default="Metro"
    )
    bio = RichTextField(blank=True, null=True)
    _revisions = GenericRelation(
        "wagtailcore.Revision", related_query_name="member_details"
    )

    @property
    def revisions(self):
        return self._revisions

    def get_url(self):
        return reverse("lametro:person", kwargs={"slug": self.person.slug})

    def __str__(self):
        loaded_obj = (
            type(self)
            .objects.select_related("person")
            .prefetch_related("person__memberships")
            .get(id=self.id)
        )
        return f"{loaded_obj.person.name}{' (current)' if loaded_obj.person.current_memberships.exists() else ''}"

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context["person"] = self.person
        context["person_details"] = self

        council_post = self.person.latest_council_membership.post
        context["qualifying_post"] = council_post.acting_label

        context["preview"] = True

        return context

    def get_preview_template(self, request, mode_name):
        return "person/person.html"


class Alert(models.Model):
    include_in_dump = True

    def __str__(self):
        return f"{self.get_type_display()} Alert - {strip_tags(self.description)[:50]}"

    TYPE_CHOICES = [
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("success", "Success"),
        ("danger", "Danger"),
        ("warning", "Warning"),
        ("info", "Info"),
    ]

    description = RichTextField()
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    expiration = models.DateTimeField(null=True, blank=True)

    panels = [
        FieldPanel(
            "type",
            help_text="Select a style for your alert.",
        ),
        FieldPanel("description"),
        FieldPanel(
            "expiration",
            help_text="Time in PT after which this alert will no longer display.",
        ),
    ]

    def content(self):
        return format_html(
            "<div class='list-display-wrapper'>"
            + expand_db_html(self.description)
            + f"<span class='button button-small alert-{self.type}'>{self.get_type_display()}</span>"
            + "</div>"
        )

    class Meta:
        ordering = ["pk"]


class CheckboxSelectMultipleList(forms.CheckboxSelectMultiple):
    def format_value(self, value):
        if isinstance(value, str):
            return value.split(",")


class EventNotice(models.Model):
    """
    A message that will show up on any event detail pages that match
    any of the event conditionals applied to each message.
    """

    include_in_dump = True

    def __str__(self):
        return f"Notice on {', '.join(self.broadcast_conditions)} and {', '.join(self.comment_conditions)} Events"

    BROADCAST_CONDITION_CHOICES = [
        ("future", "Future events"),
        ("upcoming", "Upcoming events"),
        ("ongoing", "Ongoing events"),
        ("concluded", "Concluded events"),
    ]
    COMMENT_CONDITION_CHOICES = [
        (
            "accepts_live_comment",
            "Events that accept public comment before and during the meeting",
        ),
        (
            "accepts_comment",
            "Events that accept public comment before but not during the meeting",
        ),
        ("accepts_no_comment", "Events that do not accept public comment"),
    ]

    broadcast_conditions = ArrayField(
        models.CharField(max_length=255, choices=BROADCAST_CONDITION_CHOICES),
        default=list(BROADCAST_CONDITION_CHOICES[0]),
    )
    comment_conditions = ArrayField(
        models.CharField(max_length=255, choices=COMMENT_CONDITION_CHOICES),
        default=list(COMMENT_CONDITION_CHOICES[0]),
    )
    message = RichTextField(
        features=[
            "bold",
            "italic",
            "h2",
            "h3",
            "h4",
            "ol",
            "ul",
            "hr",
            "link",
        ]
    )

    panels = [
        FieldPanel(
            "broadcast_conditions",
            widget=CheckboxSelectMultipleList(choices=BROADCAST_CONDITION_CHOICES),
            help_text=(
                "If any of the selected conditions are true for a specific event's broadcast, "
                "this message will display in its detail page."
            ),
        ),
        FieldPanel(
            "comment_conditions",
            widget=CheckboxSelectMultipleList(choices=COMMENT_CONDITION_CHOICES),
            help_text=(
                "If an event's public comment setting matches any of the selected "
                "conditions, this message will display in its detail page."
            ),
        ),
        FieldPanel("message"),
    ]

    def get_message(self):
        return strip_tags(unescape(self.message))[:50]

    def get_comment_conditions(self):
        """
        Display the longer version of the condition choices
        in the listing view for clarity
        """
        long_conditions = []
        for cond in self.comment_conditions:
            long_conditions.extend(
                [
                    choice[1]
                    for choice in self.COMMENT_CONDITION_CHOICES
                    if choice[0] == cond
                ]
            )
        return self.format_conditions(long_conditions)

    def get_broadcast_conditions(self):
        return self.format_conditions(self.broadcast_conditions)

    def format_conditions(self, conditions):
        formatted_conditions = [cond.replace("_", " ") for cond in conditions]
        return " | ".join(formatted_conditions)

    get_message.short_description = "Message"
    get_comment_conditions.short_description = "Comment conditions"
    get_broadcast_conditions.short_description = "Broadcast conditions"


class FiscalYearCalendar(models.Model):
    include_in_dump = True

    TYPE_CHOICES = [
        ("current", "Current"),
        ("upcoming", "Upcoming"),
    ]

    title = models.CharField(max_length=256, blank=True, null=True)
    calendar = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    cal_type = models.CharField(
        choices=TYPE_CHOICES, max_length=20, null=True, verbose_name="Calendar Type"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("calendar"),
        FieldPanel("cal_type"),
    ]

    def __str__(self):
        return self.title

    def clean(self):
        # Ensure that only one calendar for each type exists at a time
        model = self.__class__
        num_types = len(self.TYPE_CHOICES)
        is_new_cal = not model.objects.filter(id=self.id).exists()

        if model.objects.count() >= num_types and is_new_cal:
            raise ValidationError(
                f"Only {num_types} calendars can exist at a time. "
                "Please edit the existing calendars."
            )
        elif (filtered_cal := model.objects.filter(cal_type=self.cal_type)).exists():
            if filtered_cal.first().id != self.id:
                raise ValidationError(
                    "Only one calendar of each type can exist at a time. "
                    f"Please edit the existing '{self.cal_type}' calendar."
                )


class EventAgenda(models.Model):

    event = models.OneToOneField(
        "lametro.LAMetroEvent",
        on_delete=models.CASCADE,
        related_name="manual_agenda",
    )

    url = models.URLField(blank=True, null=True, help_text="URL to existing agenda PDF")

    document = models.ForeignKey(
        get_document_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"Manual Agenda for {self.event}"

    @property
    def document_url(self):
        return self.document.url if self.document else self.url

    @property
    def status_string(self):
        if (
            self.event.documents.exclude(note__icontains="manual")
            .filter(note__icontains="agenda")
            .exists()
        ):
            return "Superseded"
        return "Live"

    @property
    def live(self):
        return self.status_string == "Live"

    def clean(self):
        """
        Ensure that either a URL or a file is provided, but not both or neither.
        """
        if bool(self.url) == bool(self.document):
            raise ValidationError(
                "Please provide either a URL or a file, not both or neither."
            )

        if self.url:
            try:
                validator = URLValidator()
                validator(self.url)
            except ValidationError:
                raise ValidationError({"url": "Please enter a valid URL."})

    def save(self, *args, **kwargs):
        from opencivicdata.legislative.models import EventDocument

        document_obj, _ = EventDocument.objects.get_or_create(
            event=self.event, note="Manual Agenda"
        )

        document_url = self.document.url if self.document else self.url

        document_obj.links.update_or_create(
            document=document_obj, defaults={"url": document_url}
        )

        super().save(*args, **kwargs)

    def delete(self):
        self.event.documents.filter(note="Manual Agenda").delete()
        super().delete()

    def get_url(self):
        return reverse("lametro:events", kwargs={"slug": self.event.slug})


class Tooltip(models.Model):
    include_in_dump = True

    TARGET_CHOICES = [
        ("board_report_type", "Board Report Type"),
        ("fiscal_year", "Fiscal Year"),
        ("geographic_administrative_location", "Geographic / Administrative Location"),
        ("lines_ways", "Lines / Ways"),
        ("meeting", "Meeting"),
        ("metro_location", "Metro Location"),
        ("motion_by", "Motion By"),
        ("phase", "Phase"),
        ("plan_program_or_policy", "Plan, Program, or Policy"),
        ("project", "Project"),
        ("significant_date", "Significant Date"),
        ("status", "Status"),
        ("subject", "Subject"),
    ]

    target = models.CharField(
        max_length=255,
        unique=True,
        choices=TARGET_CHOICES,
    )
    content = RichTextField(
        features=[
            "bold",
            "italic",
            "link",
        ]
    )
    disabled = models.BooleanField(default=False)

    panels = [
        FieldPanel(
            "target",
            help_text=(
                "The name of the facet or topic category that this tooltip will "
                "appear next to."
            ),
        ),
        FieldPanel(
            "content",
            help_text=("The content of the tooltip."),
        ),
        FieldPanel(
            "disabled",
            help_text=("If checked, this tooltip will not display on the site."),
            icon="info-circle",
        ),
    ]

    def __str__(self):
        return self.get_target_display()

    def target_label(self):
        return self.__str__

    def short_content(self):
        shortened = strip_tags(unescape(self.content))[:50]
        if len(self.content) > 50:
            shortened += "..."
        return shortened

    def is_disabled(self):
        return "Yes" if self.disabled else "No"
