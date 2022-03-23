import csv
from tqdm import tqdm
from django.core.management.base import BaseCommand

from lametro.models import LAMetroBill


class Command(BaseCommand):

    help = "This command produces a CSV file that lists each Board Report's tags."

    def handle(self, *args, **options):

        with open('tag_analytics.csv', 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(
                ('File ID',
                 'Identifier'
                 'Title',
                 'Last Action Date',
                 'Tag Classification',
                 'Tag')
            )

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
