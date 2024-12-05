import os
from pathlib import Path
import json

from django.apps import apps
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from wagtail.images.models import Image
from wagtail.models import Site, Page, Revision


class Command(BaseCommand):
    @property
    def fixtures_dir(self):
        return Path("lametro/fixtures/")

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-type",
            default="content,images",
            type=lambda x: x.split(","),
            help="Comma-separated string of content types to load. Default: \
                  content,images. Options: content, images.",
        )
        parser.add_argument(
            "--content-fixture",
            default="cms_content.json",
            help="Name of content fixture to load. Default: cms_content.json",
        )

    @transaction.atomic
    def handle(self, **options):
        selected_content = set(options["content_type"])
        valid_content = set(["content", "images"])

        if not selected_content.issubset(valid_content):
            invalid_values = selected_content - valid_content
            raise ValueError(
                "Invalid content types: {}. Valid options are: \
                              content, images".format(
                    invalid_values
                )
            )

        for content in options["content_type"]:
            getattr(self, "load_{}".format(content))(options)

    def load_content(self, options):
        cms_content = self.fixtures_dir / options["content_fixture"]

        if not cms_content.exists():
            raise ValueError(f"No fixture file located at {cms_content}")

        with open(cms_content) as f:
            initial_data = json.load(f)

        if initial_data:
            # Delete existing content
            try:
                Site.objects.all().delete()
                Page.objects.all().delete()
                Revision.objects.all().delete()
                Image.objects.all().delete()

                for Model in apps.get_app_config("lametro").get_models():
                    if getattr(Model, "include_in_dump", False):
                        Model.objects.all().delete()

            except ObjectDoesNotExist as e:
                self.stdout.write(self.style.WARNING(e))

            call_command("loaddata", cms_content)

            self.stdout.write(self.style.SUCCESS("Initial data loaded!"))
        else:
            self.stdout.write(self.style.NOTICE("No initial data!"))

    def load_images(self, options):
        initial_images_dir = self.fixtures_dir / "initial_images"

        for root, dirs, files in os.walk(initial_images_dir):
            for filename in files:
                source_path = os.path.join(root, filename)
                dest_path = os.path.relpath(source_path, initial_images_dir)

                if default_storage.exists(dest_path):
                    self.stdout.write(
                        self.style.WARNING(
                            "{} aleady exists. Skipping...".format(dest_path)
                        )
                    )
                    continue

                else:
                    with open(source_path, "rb") as img:
                        default_storage.save(dest_path, img)
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Copied {} to default storage".format(dest_path)
                        )
                    )

        self.stdout.write(self.style.SUCCESS("Initial images loaded!"))
