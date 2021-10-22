import time

from django.core.management.base import BaseCommand
from django.db.models import F

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

        parser.add_argument('--db_only',
                            action='store_true',
                            help='Create Packet objects but do not send request to merger. Useful for staging site.')

    def handle(self, *args, **options):

        self.all_documents = options.get('all_documents')
        self.merge = not options.get('db_only')

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
                event_packet.save(merge=self.merge)
                time.sleep(1)

    def _events_to_compile(self):

        events = LAMetroEvent.objects\
            .filter(documents__note='Agenda')\
            .filter(agenda__related_entities__bill__documents__isnull=False)\
            .only('id', 'slug')\
            .distinct()

        if not self.all_documents:

            # if an event, or its related objects are changed, the
            # updated_at of the event field will update.
            #
            # so, if an agenda item is added, removed, or changed; or
            # if an agenda document is added, removed, or changed,
            # then the event's updated_at field will change
            #
            # Filtering on the updated_at field of the event will
            # catch these types of packet relevant changes, though it
            # will also sometimes catch events that had some other
            # change not relevant to the board packet.
            newer_events = events\
                .filter(packet__updated_at__lt=F('updated_at'))

            # Bills are are not updated through Pupa's event importer,
            # so if a bill is changed, it will not update an event's
            # updated_at field
            #
            # so we also need to check to see if any bill referenced
            # in an agenda has been updated.
            #
            # In particular, we want to find events where an
            # associated bill has new documents, removed documents, or
            # changed documents.
            #
            # Checking the updated_at field of the bill will do
            # this, but will also sometimes lead us to return events
            # that where the changes on associated bills were not
            # relevant to the packet
            newer_board_reports = events\
                .filter(packet__updated_at__lt=F('agenda__related_entities__bill__updated_at'))

            no_packets = events\
                .filter(packet__isnull=True)

            events = newer_events | newer_board_reports | no_packets

        return events

    def _compile_board_reports(self):

        bills = self._board_reports_to_compile()

        for bill in tqdm.tqdm(bills, desc='Board Reports'):
            bill_packet, created = BillPacket.objects.get_or_create(bill=bill)

            # The docs in a bill packet are updated on save.
            # if the doc was just created, it was also saved so
            # only call save here if the packet already existed
            if not created:
                bill_packet.save(merge=self.merge)
                time.sleep(1)

    def _board_reports_to_compile(self):

        bills = LAMetroBill.objects\
            .filter(documents__isnull=False)\
            .only('id', 'slug')\
            .distinct()

        if not self.all_documents:

            # If a document has been added, removed, or changed on a bill
            # then the bill's updated_at field will update.
            #
            # Filtering on the bill's updated_at field will catch these
            # types of packet-relevant changes, but will also catch
            # some bills that had changes not related to the pdf packet
            newer_bills = bills\
                .filter(packet__updated_at__lt=F('updated_at'))

            no_packets = bills\
                .filter(packet__isnull=True)\

            bills = newer_bills | no_packets

        return bills
