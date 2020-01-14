import csv
from datetime import datetime
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from opencivicdata.legislative.models import Bill, Event
from lametro.models import LAMetroEvent, LAMetroBill


class KeyedEvent(LAMetroEvent):
    class Meta:
        proxy = True

    @property
    def key(self):
        return (self.name, self.start_date[:10])

    @classmethod
    def transform_key(cls, key):
        # 2019-08-15 18:30:00+00 => 2019-08-15T00:00:00
        dt = datetime.strptime(key[1], '%Y-%m-%d %H:%M:%S+00').date().isoformat()
        return (key[0], dt)


class KeyedCSVGenerator(object):
    def __init__(self, infile):
        self.infile = infile
        self._cache = {}

    def yield_with_key(self, *key_fields):
        filepath = os.path.join(settings.BASE_DIR, self.infile)

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                key = tuple([row[k] for k in key_fields])
                yield key, row


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._event_generator = KeyedCSVGenerator('councilmatic_core_event.csv')

    def add_arguments(self, parser):
        parser.add_argument('--events_only',
                            action='store_true',
                            help='Import events only')

        parser.add_argument('--board_reports_only',
                            action='store_true',
                            help='Import board reports only')

    def councilmatic_entity(self, ocd_entity, entity_generator):
        entity_key = ocd_entity.key

        if entity_key in entity_generator._cache:
            return entity_generator._cache[entity_key]

        else:
            for key, event in entity_generator.yield_with_key('name', 'start_time'):
                key = ocd_entity.transform_key(key)
                entity_generator._cache[key] = event

                if key == entity_key:
                    return event

    @transaction.atomic
    def handle(self, *args, **options):
        obj_cache = []
        total_updates = 0
        entity = None

        for e in KeyedEvent.objects.all():
            entity = self.councilmatic_entity(e, self._event_generator)

            if entity is None:
                raise ValueError('Could not find event for key {}'.format(event_key))

            e.slug = entity['slug']
            obj_cache.append(e)

            if obj_cache and len(obj_cache) % 250 == 0:
                LAMetroEvent.objects.bulk_update(obj_cache, ['slug'])
                total_updates += 250
                print('Updated 250 events')
                obj_cache = []

        if obj_cache:
            LAMetroEvent.objects.bulk_update(obj_cache, ['slug'])
            total_updates += len(obj_cache)
            obj_cache = []

        print('Updated {} total events'.format(total_updates))

        try:
            assert total_updates == LAMetroEvent.objects.count()
        except AssertionError:
            print('Did not update all {} events'.format(LAMetroEvent.objects.count()))
