from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.html import format_html, strip_tags

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

    panels = [
        FieldPanel(
            "type",
            help_text="Select a style for your alert.",
        ),
        FieldPanel("description"),
    ]

    def content(self):
        return format_html(
            "<div class='list-display-wrapper'>"
            + expand_db_html(self.description)
            + f"<span class='button button-small alert-{self.type}'>{self.get_type_display()}</span>"
            + "</div>"
        )
