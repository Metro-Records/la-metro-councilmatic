# Generated by Django 3.2.25 on 2024-12-04 19:18

from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [
        ("lametro", "0016_alter_aboutpage_body"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alert",
            name="description",
            field=wagtail.fields.RichTextField(default="No content"),
            preserve_default=False,
        ),
    ]