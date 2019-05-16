from django.core.management.base import BaseCommand
from django.conf import settings
from legistar.bills import LegistarAPIBillScraper
from lametro.models import SubjectGuid, Subject


class Command(BaseCommand):
    def handle(self, *args, **options):

        scraper = LegistarAPIBillScraper()
        scraper.BASE_URL = 'https://webapi.legistar.com/v1/metrotest'
        scraper.retry_attempts = 0
        scraper.requests_per_minute = 0

        all_topics = scraper.topics()

        # Delete topics not currently in use
        current_topics = Subject.objects.values_list('subject', flat=True)
        deleted, _ = SubjectGuid.objects.exclude(name__in=current_topics).delete()

        self.stdout.write('Removing {0} stale topics'.format(deleted))

        total_created = 0
        for topic in all_topics:
            subject, created = SubjectGuid.objects.get_or_create(
                name=topic['IndexName'],
                guid=topic['api_metadata']
            )
            if created:
                total_created += 1

        self.stdout.write('{0} topics created'.format(total_created))
