import csv
from django.core.management.base import BaseCommand

from lametro.models import LAMetroBill


class Command(BaseCommand):

    help = "This command produces a CSV file that lists each Board Report's tags."

    def handle(self, *args, **options):

        with open('tag_analytics.csv', 'w', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            files = [(b.board_report.id,
                      b.identifier,
                      b.friendly_name,
                      b.last_action_date,
                      b.subject) for b in LAMetroBill.objects.all()]
            writer.writerow(['File ID', 'Identifier', 'Title', 'Last Action Date', 'Tag'])
            for report_id, identifier, title, last_action_date, tags in files:
                for tag in tags:
                    writer.writerow([
                        str(report_id),
                        identifier,
                        title,
                        last_action_date,
                        tag,
                    ])
