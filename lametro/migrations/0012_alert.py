# Generated by Django 3.2.19 on 2023-09-11 14:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lametro", "0011_relatebillsubject"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
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
                ("description", models.TextField(blank=True, null=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("primary", "Primary"),
                            ("secondary", "Secondary"),
                            ("success", "Success"),
                            ("danger", "Danger"),
                            ("warning", "Warning"),
                            ("info", "Info"),
                        ],
                        max_length=255,
                    ),
                ),
            ],
        ),
    ]
