import sqlalchemy as sa
from urllib.request import urlopen
from io import StringIO, BytesIO
import logging
import requests
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from councilmatic.settings import MERGER_BASE_URL

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

            LOGGER.info(self.style.NOTICE("Sending POST requests to metro-pdf-merger."))
            for idx, el in enumerate(report_packet_raw):
                board_report_slug = 'ocd-bill-' + el[0].split('/')[1]
                filenames = el[1]

                if len(filenames) > 1:
                    # Put the filenames inside a data structure, and send a post request with the slug.
                    data = json.dumps(filenames)
                    url = MERGER_BASE_URL + '/merge_pdfs/' + board_report_slug
                    requests.post(url, data=data)

        if not options['board_reports_only']:
            LOGGER.info(self.style.NOTICE("Finding all documents for event agendas."))
            LOGGER.info(self.style.NOTICE("............"))
            if options['all_documents']:
                event_packet_raw = self.findEventAgendaPacket(all_documents=True)
            else:
                event_packet_raw = self.findEventAgendaPacket()

            LOGGER.info(self.style.NOTICE("Sending POST requests to metro-pdf-merger."))
            for idx, el in enumerate(event_packet_raw):
                event_slug = 'ocd-event-' + el[0].split('/')[1]
                event_agenda = el[1]
                filenames = el[2]
                filenames.insert(0, str(event_agenda))

                data = json.dumps(filenames)
                url = MERGER_BASE_URL + '/merge_pdfs/' + event_slug
                requests.post(url, data=data)
        LOGGER.info(self.style.SUCCESS(".........."))
        LOGGER.info(self.style.SUCCESS("Command complete. Excellent work, everyone. Go to metro-pdf-merger for results!"))
        print("Command done at: ", datetime.now())


    def findBoardReportPacket(self, all_documents=False):
        board_reports = []
        query = ''

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

            board_reports = self.connection.execute(sa.text(query))
        else:
            # (1) Get ids for board reports that need new PDF packets.
            grab_ids_query = '''
            SELECT bill_id FROM new_billdocument GROUP BY bill_id
            '''

            bill_ids_proxy = self.connection.execute(sa.text(grab_ids_query))
            bill_ids_results = bill_ids_proxy.fetchall()
            bill_ids_str = ''

            if bill_ids_results:
                for el in bill_ids_results:
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
        event_agendas = []

        if all_documents:
            query = '''
                WITH packet_info AS (
                    SELECT DISTINCT
                        agenda_item.event_id,
                        agenda_item.order as item_order,
                        d_bill.url,
                        d_bill.bill_id,
                        d_event.url as event_agenda,
                        CASE
                        WHEN trim(lower(d_bill.note)) LIKE 'board report%' THEN '1'
                        WHEN trim(lower(d_bill.note)) LIKE '0%' THEN 'z'
                        ELSE trim(lower(d_bill.note))
                        END AS note
                    FROM councilmatic_core_billdocument AS d_bill
                    INNER JOIN councilmatic_core_eventagendaitem as agenda_item
                    USING (bill_id)
                    INNER JOIN councilmatic_core_eventdocument as d_event
                    USING (event_id)
                    )
                SELECT
                    event_id,
                    event_agenda,
                    array_agg(url ORDER BY item_order, bill_id, note)
                FROM packet_info
                GROUP BY event_id, event_agenda
            '''

            event_agendas = self.connection.execute(sa.text(query))
        else:
            # The compile script typically runs without an `all_documents` argument.
            # In those cases, the query should only grab the related event_ids for new bill and event documents.
            grab_events = '''
                SELECT DISTINCT event_id
                FROM councilmatic_core_eventagendaitem
                INNER JOIN new_billdocument
                USING (bill_id)
                UNION
                SELECT DISTINCT event_id
                FROM new_eventdocument
            '''
            event_ids_proxy = self.connection.execute(sa.text(grab_events))
            event_ids_results = [el[0] for el in event_ids_proxy.fetchall() if el[0]]

            if event_ids_results:
                query = '''
                    WITH packet_info AS (
                        SELECT DISTINCT
                            agenda_item.event_id,
                            agenda_item.order as item_order,
                            d_bill.url,
                            d_bill.bill_id,
                            d_event.url as event_agenda,
                            CASE
                            WHEN trim(lower(d_bill.note)) LIKE 'board report%' THEN '1'
                            WHEN trim(lower(d_bill.note)) LIKE '0%' THEN 'z'
                            ELSE trim(lower(d_bill.note))
                            END AS note
                        FROM councilmatic_core_billdocument AS d_bill
                        INNER JOIN councilmatic_core_eventagendaitem as agenda_item
                        USING (bill_id)
                        INNER JOIN councilmatic_core_eventdocument as d_event
                        USING (event_id)
                        WHERE agenda_item.event_id in :event_ids
                        )
                    SELECT
                        event_id,
                        event_agenda,
                        array_agg(url ORDER BY item_order, bill_id, note)
                    FROM packet_info
                    GROUP BY event_id, event_agenda
                '''

                params = {'event_ids': tuple(event_ids_results)}
            
                event_agendas = self.connection.execute(sa.text(query), **params)

        return event_agendas
