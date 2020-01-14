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

    def __str__(self):
        return 'Event'

    @property
    def key(self):
        return (self.name, self.start_date[:10])

    @classmethod
    def transform_key(cls, key):
        # 2019-08-15 18:30:00+00 => 2019-08-15T00:00:00
        dt = datetime.strptime(key[1], '%Y-%m-%d %H:%M:%S+00').date().isoformat()
        return (key[0], dt)


class KeyedBill(LAMetroBill):
    class Meta:
        proxy = True

    def __str__(self):
        return 'Bill'

    @property
    def key(self):
        return (self.identifier,)

    @classmethod
    def transform_key(cls, key):
        return key


class KeyedCSVGenerator(object):
    def __init__(self, infile, key_fields):
        self.infile = infile
        self.key_fields = key_fields
        self._cache = {}

    def yield_with_key(self):
        filepath = os.path.join(settings.BASE_DIR, self.infile)

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                key = tuple([row[k] for k in self.key_fields])
                yield key, row


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._event_generator = KeyedCSVGenerator('councilmatic_core_event.csv', ('name', 'start_time'))
        self._bill_generator = KeyedCSVGenerator('councilmatic_core_bill.csv', ('identifier',))

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
            for key, entity in entity_generator.yield_with_key():
                key = ocd_entity.transform_key(key)
                entity_generator._cache[key] = entity

                if key == entity_key:
                    return entity

    @transaction.atomic
    def handle(self, *args, **options):
        self._migrate(KeyedEvent, self._event_generator)
        self._migrate(KeyedBill, self._bill_generator)

    def _migrate(self, model, generator):
        obj_cache = []
        total_updates = 0

        for obj in model.objects.all():
            entity = self.councilmatic_entity(obj, generator)

            if entity is None:
                print('Could not find match for {0} object {1}'.format(obj, obj.key))
                continue

            obj.slug = entity['slug']
            obj_cache.append(obj)

            if obj_cache and len(obj_cache) % 250 == 0:
                model.objects.bulk_update(obj_cache, ['slug'])
                total_updates += 250
                print('Updated 250 objects')
                obj_cache = []

        if obj_cache:
            model.objects.bulk_update(obj_cache, ['slug'])
            total_updates += len(obj_cache)
            obj_cache = []

        event_count = model.objects.count()

        try:
            assert total_updates == event_count
        except AssertionError:
            print('Found only {0} updates for {1} total objects of type {2}'.format(total_updates, event_count, model))
        else:
            print('Updated all {0} objects of type {1}'.format(event_count, model))
