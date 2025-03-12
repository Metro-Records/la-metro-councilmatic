from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django import forms
from django.utils.html import format_html, strip_tags
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from html import unescape

from wagtail.models import Page, PreviewableMixin, DraftStateMixin, RevisionMixin
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.rich_text import expand_db_html

from lametro.blocks import ArticleBlock


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

    title = models.CharField(max_length=256, blank=True, null=True)
    calendar = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("calendar"),
    ]

    def __str__(self):
        return self.title

    def clean(self):
        # Ensure that only one calendar exists at a time
        model = self.__class__
        if model.objects.count() > 0 and self.id != model.objects.get().id:
            raise ValidationError(
                "Only one calendar can exist at a time. "
                "Please edit the existing calendar object."
            )
