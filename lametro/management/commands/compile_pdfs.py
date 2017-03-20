import sqlalchemy as sa
from urllib.request import urlopen
from io import StringIO, BytesIO
import logging
import requests
import json

from django.core.management.base import BaseCommand
from django.conf import settings

LOGGER = logging.getLogger(__name__)

DB_CONN = 'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'

ENGINE = sa.create_engine(DB_CONN.format(**settings.DATABASES['default']),
                          convert_unicode=True,
                          server_side_cursors=True)

class Command(BaseCommand):

    help = "This command compiles PDF packets for LA Metro events and board reports. By default, the command queries the new_billdocument table."


    def add_arguments(self, parser):

        parser.add_argument('--all_documents',
                            action='store_true',
                            help='Compile all board report and event packets')

        parser.add_argument('--events_only',
                            action='store_true',
                            help='Compile new event packets only')

        parser.add_argument('--board_reports_only',
                            action='store_true',
                            help='Compile new board report packets only')


    def handle(self, *args, **options):

        self.connection = ENGINE.connect()

        if not options['events_only']:
            LOGGER.info(self.style.NOTICE("Finding all documents for board reports."))
            LOGGER.info(self.style.NOTICE("............"))
            if options['all_documents']:
                report_packet_raw = self.findBoardReportPacket(all_documents=True)
            else:
                report_packet_raw = self.findBoardReportPacket()

            LOGGER.info(self.style.NOTICE("Merging PDFs."))
            for idx, el in enumerate(report_packet_raw):
                board_report_slug = 'ocd-bill-' + el[0].split('/')[1]
                filenames = el[1]
                if len(filenames) > 1:
                    # Put the filenames inside a data structure, and send a post request with the slug.
                    data = json.dumps(filenames)
                    url = 'http://0.0.0.0:5000/merge_pdfs/' + board_report_slug
                    r = requests.post(url, data=data)

        if not options['board_reports_only']:
            LOGGER.info(self.style.NOTICE("Finding all documents for event agendas."))
            LOGGER.info(self.style.NOTICE("............"))
            if options['all_documents']:
                event_packet_raw = self.findEventAgendaPacket(all_documents=True)
            else:
                event_packet_raw = self.findEventAgendaPacket()

            LOGGER.info(self.style.NOTICE("Merging PDFs."))
            for idx, el in enumerate(event_packet_raw):
                event_slug = 'ocd-event-' + el[0].split('/')[1]
                event_agenda = el[1]
                filenames = el[2]
                filenames.insert(0, str(event_agenda))

                data = json.dumps(filenames)
                url = 'http://0.0.0.0:5000/merge_pdfs/' + event_slug
                r = requests.post(url, data=data)


        LOGGER.info(self.style.SUCCESS(".........."))
        LOGGER.info(self.style.SUCCESS("Job complete. Excellent work, everyone."))


    def findBoardReportPacket(self, all_documents=False):

        if all_documents:
            query = '''
            SELECT
              bill_id,
              array_agg(url ORDER BY note)
            FROM (
              SELECT
                bill_id,
                url,
                CASE
                WHEN trim(lower(note)) LIKE 'board report%' THEN '1'
                WHEN trim(lower(note)) LIKE '0%' THEN 'z'
                ELSE trim(lower(note))
                END AS note
              FROM councilmatic_core_billdocument
            ) AS subq
            GROUP BY bill_id
            '''
        else:
            # (1) Get ids for board reports that need new PDF packets.
            grab_ids_query = '''
            SELECT bill_id FROM new_billdocument GROUP BY bill_id
            '''

            bill_ids_results = self.connection.execute(sa.text(grab_ids_query))
            bill_ids_str = ''

            for idx, el in enumerate(bill_ids_results):
                bill_ids_str += "'" + str(el.values()[0]) + "',"

            psql_ready_ids = bill_ids_str[:-1]

            # (2) Create a query for bill documents, but only for the specified bill_ids.
            query = '''
            SELECT
              bill_id,
              array_agg(url ORDER BY note)
            FROM (
              SELECT
                bill_id,
                url,
                CASE
                WHEN trim(lower(note)) LIKE 'board report%' THEN '1'
                WHEN trim(lower(note)) LIKE '0%' THEN 'z'
                ELSE trim(lower(note))
                END AS note
              FROM councilmatic_core_billdocument
            ) AS subq
            WHERE bill_id in ( {} )
            GROUP BY bill_id
            '''.format(psql_ready_ids)

        board_reports = self.connection.execute(sa.text(query))

        return board_reports


    def findEventAgendaPacket(self, all_documents=False):

        if all_documents:
            query = '''
            SELECT
                event_id,
                event_agenda,
                array_agg(url ORDER BY identifier, bill_id, note)
            FROM (
                SELECT
                    b.identifier,
                    i.event_id,
                    d_bill.url,
                    d_bill.bill_id,
                    d_event.url as event_agenda,
                    CASE
                    WHEN trim(lower(d_bill.note)) LIKE 'board report%' THEN '1'
                    WHEN trim(lower(d_bill.note)) LIKE '0%' THEN 'z'
                    ELSE trim(lower(d_bill.note))
                    END AS note
                FROM councilmatic_core_billdocument AS d_bill
                INNER JOIN councilmatic_core_eventagendaitem as i
                ON i.bill_id=d_bill.bill_id
                INNER JOIN councilmatic_core_eventdocument as d_event
                ON i.event_id=d_event.event_id
                INNER JOIN councilmatic_core_bill AS b
                ON d_bill.bill_id=b.ocd_id
                ) AS subq
            GROUP BY event_id, event_agenda
            '''
        else:
            # TODO: add a query for raw tables
            grab_ids_query = '''
            SELECT bill_id FROM new_billdocument GROUP BY bill_id
            '''

            bill_ids_results = self.connection.execute(sa.text(grab_ids_query))
            bill_ids_str = ''

            for idx, el in enumerate(bill_ids_results):
                bill_ids_str += "'" + str(el.values()[0]) + "',"

            psql_ready_ids = bill_ids_str[:-1]

            query = '''
            SELECT
                event_id,
                event_agenda,
                array_agg(url ORDER BY identifier, bill_id, note)
            FROM (
                SELECT
                    b.identifier,
                    i.event_id,
                    d_bill.url,
                    d_bill.bill_id,
                    d_event.url as event_agenda,
                    CASE
                    WHEN trim(lower(d_bill.note)) LIKE 'board report%' THEN '1'
                    WHEN trim(lower(d_bill.note)) LIKE '0%' THEN 'z'
                    ELSE trim(lower(d_bill.note))
                    END AS note
                FROM councilmatic_core_billdocument AS d_bill
                INNER JOIN councilmatic_core_eventagendaitem as i
                ON i.bill_id=d_bill.bill_id
                INNER JOIN councilmatic_core_eventdocument as d_event
                ON i.event_id=d_event.event_id
                INNER JOIN councilmatic_core_bill AS b
                ON d_bill.bill_id=b.ocd_id
                WHERE d_bill.bill_id in ( {} )
                ) AS subq
            GROUP BY event_id, event_agenda
            '''.format(psql_ready_ids)

        event_agendas = self.connection.execute(sa.text(query))

        return event_agendas

