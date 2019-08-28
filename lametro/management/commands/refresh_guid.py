from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from legistar.bills import LegistarAPIBillScraper
from lametro.models import SubjectGuid, Subject


class Command(BaseCommand):
    def handle(self, *args, **options):

        scraper = LegistarAPIBillScraper()
        scraper.BASE_URL = 'https://webapi.legistar.com/v1/metro'
        scraper.retry_attempts = 0
        scraper.requests_per_minute = 0

        all_topics = scraper.topics()

        # Delete topics not currently in use
        current_topics = Subject.objects.values_list('subject', flat=True)
        deleted, _ = SubjectGuid.objects.exclude(name__in=current_topics).delete()

        self.stdout.write('Removed {0} stale topics'.format(deleted))

        total_created = 0
        total_updated = 0
        total_noop = 0

        for topic in all_topics:
            try:
                subject, created = SubjectGuid.objects.get_or_create(
                    name=topic['IndexName'],
                    guid=topic['api_metadata']
                )
            except IntegrityError as e:
                # This exception will be raised if get_or_create tries to create
                # a SubjectGuid with a name that already exists. The Legistar
                # API should not contain duplicates, i.e., the GUID has changed.
                # Update the GUID on the existing topic.
                subject = SubjectGuid.objects.get(name=topic['IndexName'])
                subject.guid = topic['api_metadata']
                subject.save()
                total_updated += 1
            else:
                if created:
                    total_created += 1
                else:
                    total_noop += 1

        self.stdout.write('Created {0} new topics'.format(total_created))
        self.stdout.write('Updated {0} existing topics'.format(total_updated))
        self.stdout.write('No-op {0} topics'.format(total_noop))
