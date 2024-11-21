from django.db import models

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel

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

    panels = [FieldPanel("type"), FieldPanel("description", widget=MarkdownTextarea)]
