from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.utils.html import format_html, strip_tags

from wagtail.models import Page
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.rich_text import expand_db_html

from lametro.blocks import ArticleBlock
from .legislative import LAMetroOrganization, LAMetroPost


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


class BoardOfDirectorsPage(Page):
    include_in_dump = True

    search_title = models.CharField(max_length=50)
    search_examples = models.CharField(max_length=150)
    geography_tooltip = RichTextField()

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("search_title"),
                FieldPanel("search_examples"),
            ],
            heading="Search bar",
            help_text="Customize the text surrounding the board member search bar",
        ),
        FieldPanel("geography_tooltip"),
    ]

    def get_map_context(self):
        maps = {
            "MAP_CONFIG": settings.MAP_CONFIG,
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

    def get_table_context(self):
        board = LAMetroOrganization.objects.get(name=settings.OCD_CITY_COUNCIL_NAME)

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

        return {
            "posts": sorted(
                sortable_memberships, key=lambda x: (x.index, x.person.family_name)
            )
        }

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context.update(self.get_map_context())
        context.update(self.get_table_context())

        board = LAMetroOrganization.objects.get(name=settings.OCD_CITY_COUNCIL_NAME)
        context["recent_activity"] = board.actions.order_by(
            "-date", "-bill__identifier", "-order"
        )
        context["recent_events"] = board.recent_events

        return context


class BoardMemberPage(Page):
    include_in_dump = True

    # headshot
    # bio
    # other text?


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
