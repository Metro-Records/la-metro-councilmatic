# Generated by Django 3.2.25 on 2024-12-11 21:40

import django.contrib.postgres.fields
from django.db import migrations, models
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("lametro", "0017_alter_alert_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventNotice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "broadcast_conditions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("future", "Future events"),
                                ("upcoming", "Upcoming events"),
                                ("ongoing", "Ongoing events"),
                                ("concluded", "Concluded events"),
                            ],
                            max_length=255,
                        ),
                        default=["future", "Future events"],
                        size=None,
                    ),
                ),
                (
                    "comment_conditions",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                (
                                    "accepts_live_comment",
                                    "Events that accept live public comments",
                                ),
                                (
                                    "accepts_comment",
                                    "Events that accept public comments when not live",
                                ),
                                (
                                    "accepts_no_comment",
                                    "Events that do not accept public comments at all",
                                ),
                            ],
                            max_length=255,
                        ),
                        default=[
                            "accepts_live_comment",
                            "Events that accept live public comments",
                        ],
                        size=None,
                    ),
                ),
                ("message", wagtail.fields.RichTextField()),
            ],
        ),
    ]