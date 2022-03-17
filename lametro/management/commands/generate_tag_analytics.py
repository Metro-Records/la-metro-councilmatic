import csv
from tqdm import tqdm
from django.core.management.base import BaseCommand

from lametro.models import LAMetroBill


class Command(BaseCommand):

    help = "This command produces a CSV file that lists each Board Report's tags."

    def handle(self, *args, **options):

        with open('tag_analytics.csv', 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            files = []
            for bill in LAMetroBill.all_objects.all():
                if bill.board_report:
                    files.append(
                        (bill.board_report.id,
                         bill.identifier,
                         bill.friendly_name,
                         bill.last_action_date,
                         bill.subject)
                    )

            writer.writerow(['File ID', 'Identifier', 'Title', 'Last Action Date', 'Tag'])
            for report_id, identifier, title, last_action_date, tags in tqdm(files):
                for tag in tags:
                    writer.writerow([
                        str(report_id),
                        identifier,
                        title,
                        last_action_date,
                        tag,
                    ])
