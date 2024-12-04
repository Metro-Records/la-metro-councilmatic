from django.db import models
from django.utils.html import format_html, strip_tags

from wagtail.models import Page
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
