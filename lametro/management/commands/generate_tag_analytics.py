import csv
from io import StringIO
from datetime import datetime
from tqdm import tqdm

from django.conf import settings
from django.core.management.base import BaseCommand

from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from lametro.models import LAMetroBill


class Command(BaseCommand):

    help = "This command produces a CSV file that lists each Board Report's tags and \
        uploads it to the 'LA Metro Reports' folder in Google Drive."

    def handle(self, *args, **options):

        csv_string = self.generate_tag_analytics()
        date = datetime.today().strftime('%m_%d_%y')
        output_file_name = f'{date}_tag_analytics.csv'


        file_metadata = {
            'name': output_file_name,
            'parents': [settings.REMOTE_ANALYTICS_FOLDER]
        }
        drive_service = self.get_google_drive()

        if not drive_service:
            return

        media = MediaIoBaseUpload(csv_string, mimetype='text/csv')
        drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully uploaded {output_file_name}!')
        )

    def generate_tag_analytics(self):
        """Returns a CSV-formatted byte stream of the tag analytics"""

        csv_string = StringIO()
        writer = csv.writer(csv_string, delimiter=',')
        writer.writerow(
            ('File ID',
             'Identifier'
             'Title',
             'File Name',
             'Last Action Date',
             'Tag Classification',
             'Tag')
        )

        self.stdout.write('\nGenerating tag analytics...')
        for bill in tqdm(LAMetroBill.objects.all()):
            for tag in bill.rich_topics:
                writer.writerow(
                    (bill.board_report.id,
                     bill.identifier,
                     bill.friendly_name,
                     bill.last_action_date,
                     tag.classification,
                     tag.name)
                )

        return csv_string

    def get_google_drive(self):
        """Authenticates a service account and returns a Google Drive object."""

        SCOPES = [
            'https://www.googleapis.com/auth/drive',
        ]

        try:
            credentials = service_account.Credentials.from_service_account_file(
                    settings.SERVICE_ACCOUNT_KEY_PATH
                ).with_scopes(SCOPES)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Service account key file not found.'))
            return

        if not credentials:
            self.stdout.write(self.style.ERROR('Could not generate credentials!'))
            return None

        return build('drive', 'v3', credentials=credentials)
