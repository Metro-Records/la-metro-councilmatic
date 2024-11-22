from django.db import models
from django.utils.html import format_html

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel

from wagtailmarkdown.utils import render_markdown
from wagtailmarkdown.widgets import MarkdownTextarea

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
        return f"{self.type} Alert - {self.description[:50]}"

    TYPE_CHOICES = [
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("success", "Success"),
        ("danger", "Danger"),
        ("warning", "Warning"),
        ("info", "Info"),
    ]

    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES)

    panels = [
        FieldPanel(
            "type",
            help_text="Select a style for your alert.",
        ),
        FieldPanel("description", widget=MarkdownTextarea),
    ]

    def content(self):
        return format_html(
            "<div class='list-display-wrapper'>"
            + render_markdown(self.description)
            + f"<span class='button alert-{self.type}'>{self.get_type_display()}</span>"
            + "</div>"
        )
