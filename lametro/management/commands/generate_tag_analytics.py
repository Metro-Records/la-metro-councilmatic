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
from lametro.exceptions import DriveBuildError, UploadError


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

        try:
            drive_service = self.get_google_drive()
            file = self.upload_file_bytes(drive_service, csv_string, file_metadata)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully uploaded {output_file_name}!')
            )
        except DriveBuildError as e:
            self.stdout.write(
                self.style.ERROR(f'Unable to connect to Google Drive!')
            )
            raise
        except HttpError as e:
            self.stdout.write(
                self.style.ERROR(f'HTTP Error!')
            )
            raise
        except UploadError as e:
            self.stdout.write(
                self.style.ERROR(f'Unable to upload the file: {e}')
            )
            raise

    def generate_tag_analytics(self):
        """Returns a CSV-formatted byte stream of the tag analytics"""

        csv_string = StringIO()
        writer = csv.writer(csv_string, delimiter=',')
        writer.writerow(
            ('File ID',
             'Identifier'
             'File Name',
             'Last Action Date',
             'Tag',
             'Tag Classification')
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

            return build('drive', 'v3', credentials=credentials)

        except Exception as e:
            raise DriveBuildError

    def upload_file_bytes(self, drive, file, file_metadata):
        """Uploads a byte stream to Google Drive."""

        media = MediaIoBaseUpload(file, mimetype='text/csv')
        file = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        if 'error' in file:
            raise UploadError(file)

        return file
