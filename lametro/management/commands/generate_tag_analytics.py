import csv
from io import StringIO, BytesIO
from datetime import datetime
from tqdm import tqdm
from time import sleep
from shutil import copyfileobj

from django.conf import settings
from django.core.management.base import BaseCommand

from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account

from lametro.models import LAMetroBill
from lametro.exceptions import UploadError


class Command(BaseCommand):

    help = "This command produces a CSV file that lists each Board Report's tags and \
        uploads it to the 'LA Metro Reports' folder in Google Drive."

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--local',
            action='store_true',
            help='Output the generated CSV file to the current directory'
        )

    def handle(self, *args, **options):
        local = options['local']

        csv_string = self.generate_tag_analytics()
        date = datetime.today().strftime("%m_%d_%y")
        output_file_name = f"{date}_tag_analytics.csv"

        if local:
            with open(output_file_name, 'wb') as f:
                copyfileobj(csv_string, f)

            return

        file_metadata = {
            "name": output_file_name,
            "parents": [settings.REMOTE_ANALYTICS_FOLDER],
        }

        try:
            drive_service = self.get_google_drive()
            self.upload_file_bytes(drive_service, csv_string, file_metadata)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully uploaded {output_file_name}!")
            )
        except UploadError as e:
            self.stdout.write(
                self.style.ERROR(f"Unable to upload the file to Google Drive: {e}")
            )
            raise

    def generate_tag_analytics(self):
        """Returns a CSV-formatted byte stream of the tag analytics"""

        csv_string = StringIO()
        writer = csv.writer(csv_string, delimiter=",")
        writer.writerow(
            (
                "File GUID",
                "File ID",
                "Matter ID",
                "File Name",
                "Last Action Date",
                "Tag",
                "Tag GUID",
                "Tag Classification",
            )
        )

        self.stdout.write("\nGenerating tag analytics...")

        for bill in tqdm(LAMetroBill.objects.iterator(chunk_size=200)):
            for tag in bill.rich_topics:
                writer.writerow(
                    (
                        bill.board_report.id,
                        bill.identifier,
                        self.get_matter_id(bill.api_source.url),
                        bill.friendly_name,
                        bill.last_action_date,
                        tag.name,
                        tag.guid,
                        self.get_tag_classification(tag)
                    )
                )

        csv_string.seek(0)

        return BytesIO(csv_string.read().encode("utf-8"))

    def get_matter_id(self, source_url):
        """Parses out the matter ID from a bill's source URL."""
        prefix = "https://webapi.legistar.com/v1/metro/matters/"
        return source_url.split(prefix)[-1]

    def get_tag_classification(self, tag):
        """Strips out '_exact' from the end of a tag's classification."""

        if tag.classification.endswith('_exact'):
            return tag.classification[:-6]

        return tag.classification

    def get_google_drive(self):
        """Authenticates a service account and returns a Google Drive object."""

        SCOPES = [
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = service_account.Credentials.from_service_account_file(
            settings.SERVICE_ACCOUNT_KEY_PATH
        ).with_scopes(SCOPES)

        return build("drive", "v3", credentials=credentials)

    def upload_file_bytes(self, drive, file, file_metadata):
        """Uploads a byte stream to Google Drive."""

        media = MediaIoBaseUpload(file, mimetype="text/csv")

        result = (
            drive.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        if "error" in result:
            raise UploadError(result)

        return result
