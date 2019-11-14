from django.core.management.base import BaseCommand
import django.db.models as models
from django.db.models import F, Case, When
from django.db.models.functions import Cast

from lametro.models import LAMetroBill, BillPacket, LAMetroEvent, EventPacket

import tqdm

class Command(BaseCommand):

    help = "This command compiles PDF packets for LA Metro events and board reports."

    def add_arguments(self, parser):

        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--events_only',
            action='store_true',
            help='Compile new event packets only')
        group.add_argument('--board_reports_only',
                           action='store_true',
                           help='Compile new board report packets only')

        parser.add_argument('--all_documents',
                            action='store_true',
                            help='Compile all board report and event packets')

    def handle(self, *args, **options):

        self.all_documents = options.get('all_documents')

        if options.get('events_only'):
            self._compile_events()
        elif options.get('board_reports_only'):
            self._compile_board_reports()
        else:
            self._compile_events()
            self._compile_board_reports()
        
    def _compile_events(self):

        events = self._events_to_compile()

        for event in tqdm.tqdm(events, desc='Events'):
            event_packet, created = EventPacket.objects.get_or_create(event=event)
            # The docs in an event packet are updated on save.
            # if the doc was just created, it was also saved so
            # only save if the packet already existed
            if not created:
                event_packet.save()

    def _events_to_compile(self):
    
        if self.all_documents:
            events = LAMetroEvent.objects\
                .filter(documents__note='Agenda')\
                .filter(agenda__related_entities__bill__documents__isnull=False)\
                .only('id', 'slug')\
                .distinct()

        else:
            newer_board_reports = LAMetroEvent.objects\
                .annotate(documents_date=Cast(
                    Case(
                        When(agenda__related_entities__bill__documents__date='', then=None),
                        default=F('agenda__related_entities__bill__documents__date'),
                        output_field=models.CharField()
                    ),
                    models.DateTimeField()))\
                .filter(documents__note='Agenda')\
                .filter(packet__updated_at__lt=F('documents_date'))\
                .only('id', 'slug')\
                .distinct()

            newer_agendas = LAMetroEvent.objects\
                .annotate(agenda_date=Cast(
                    Case(
                        When(documents__date='', then=None),
                        default=F('documents__date'),
                        output_field=models.CharField()
                    ),
                    models.DateTimeField()))\
                .filter(agenda__related_entities__bill__documents__isnull=False)\
                .filter(documents__note='Agenda',
                        packet__updated_at__lt=F('agenda_date'))\
                .only('id', 'slug')\
                .distinct()

            no_packets = LAMetroEvent.objects\
                .filter(agenda__related_entities__bill__documents__isnull=False)\
                .filter(documents__note='Agenda')\
                .filter(packet__isnull=True)\
                .distinct()

            events = newer_board_reports | newer_agendas | no_packets

        return events

    def _compile_board_reports(self):

        bills = self._board_reports_to_compile()

        for bill in tqdm.tqdm(bills, desc='Board Reports'):
            bill_packet, created = BillPacket.objects.get_or_create(bill=bill)

            # The docs in an bill packet are updated on save.
            # if the doc was just created, it was also saved so
            # only save if the packet already existed
            if not created:
                bill_packet.save()

    def _board_reports_to_compile(self):
            
        if self.all_documents:
            bills = LAMetroBill.objects\
                .filter(documents__isnull=False)\
                .only('id', 'slug')\
                .distinct()

        else:
            bills_needing_updating = LAMetroBill.objects\
                .filter(documents__isnull=False)\
                .annotate(documents_date=Cast(
                    Case(
                        When(documents__date='', then=None),
                        default=F('documents__date'),
                        output_field=models.CharField()
                    ),
                    models.DateTimeField()))\
                .filter(packet__updated_at__lt=F('documents_date'))\
                .only('id', 'slug')\
                .distinct()

            bills_without_packets = LAMetroBill.objects\
                .filter(packet__isnull=True)\
                .distinct()

            bills = bills_needing_updating | bills_without_packets

        return bills
