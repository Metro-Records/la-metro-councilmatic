import sqlalchemy as sa
from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import StringIO, BytesIO
from subprocess import call
import signal
import sys
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
    help = "This command compiles PDFs for the LA Metro Agenda and Board Report packets."


    def add_arguments(self, parser):

        parser.add_argument('--all_documents',
                            action='store_true',
                            help='Compile all documents for board report and event packets')

        parser.add_argument('--events_only',
                            action='store_true',
                            help='Compile all documents for event packets')

        parser.add_argument('--board_reports_only',
                            action='store_true',
                            help='Compile all documents for board report packets')


    def handle(self, *args, **options):

        self.connection = ENGINE.connect()

        # if not options['events_only']:
        #     LOGGER.info(self.style.NOTICE("Finding all documents for board reports."))
        #     LOGGER.info(self.style.NOTICE("............"))
        #     if options['all_documents']:
        #         report_packet_raw = self.findBoardReportPacket(all_documents=True)
        #     else:
        #         report_packet_raw = self.findBoardReportPacket()

        #     LOGGER.info(self.style.NOTICE("Merging PDFs."))
        #     for idx, el in enumerate(report_packet_raw):
        #         board_report_slug = 'board-report-' + el[0].split('/')[1]
        #         filenames = el[1]
        #         if len(filenames) > 1:
        #             # Here, we put the filenames inside a data structure, and we send a post request with the slug.
        #             data = json.dumps(filenames)
        #             url = 'http://0.0.0.0:5000/merge_pdfs/' + board_report_slug
        #             r = requests.post(url, data=data)



        # data = json.dumps(["https://metro.legistar.com/ViewReport.ashx?M=R&N=TextL5&GID=557&ID=3044&GUID=LATEST&Title=Board+Report", "http://metro.legistar1.com/metro/attachments/806ee185-bdce-46f4-92a0-1b85e1d2ba48.pdf", "http://metro.legistar1.com/metro/attachments/5951913e-bc43-411a-9d6c-da89eead58fb.pdf"])
        # url = 'http://0.0.0.0:5000/merge_pdfs/' + '12345678910'
        # print(json.dumps(data))
        # r = requests.post(url, data=data)
        # print(r.text)

        #     LOGGER.info(self.style.NOTICE("Merging PDFs."))
        #     for idx, el in enumerate(report_packet_raw):
        #         board_report_id = el[0]
        #         filenames = el[1]
        #         if len(filenames) > 1:
        #             self.makePacket(board_report_id, filenames)



        if not options['board_reports_only']:
            LOGGER.info(self.style.NOTICE("Finding all documents for event agendas."))
            LOGGER.info(self.style.NOTICE("............"))
            if options['all_documents']:
                event_packet_raw = self.findEventAgendaPacket(all_documents=True)
            else:
                event_packet_raw = self.findEventAgendaPacket()

            LOGGER.info(self.style.NOTICE("Merging PDFs."))
            for idx, el in enumerate(event_packet_raw):
                event_slug = 'event-' + el[0].split('/')[1]
                event_agenda = el[1]
                filenames = el[2]
                filenames.insert(0, str(event_agenda))

                data = json.dumps(filenames)
                url = 'http://0.0.0.0:5000/merge_pdfs/' + event_slug
                r = requests.post(url, data=data)




        # if not options['board_reports_only']:
        #     LOGGER.info(self.style.NOTICE("Finding all documents for event agendas."))
        #     LOGGER.info(self.style.NOTICE("............"))
        #     if options['all_documents']:
        #         event_packet_raw = self.findEventAgendaPacket(all_documents=True)
        #     else:
        #         event_packet_raw = self.findEventAgendaPacket()


        #     LOGGER.info(self.style.NOTICE("Merging PDFs."))
        #     for idx, el in enumerate(event_packet_raw):
        #         event_slug = 'event-' + el[0].split('/')[1]
        #         print(event_slug)
        #         filenames = el[1]
        #         print(filenames)
        #         if len(filenames) > 1:
        #             # Here, we put the filenames inside a data structure, and we send a post request with the slug.
        #             data = json.dumps(filenames)
        #             print(data)
        #             url = 'http://0.0.0.0:5000/merge_pdfs/' + event_slug
        #             r = requests.post(url, data=data)

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
            # TODO: add a query for raw tables.
            query = ''

        board_reports = self.connection.execute(sa.text(query))

        return board_reports


    def findEventAgendaPacket(self, all_documents=False):
        # If we want to include the note in a nested array: SELECT i.event_id, array_agg(array[d.note, d.url])
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
            query = ''

        event_agendas = self.connection.execute(sa.text(query))

        return event_agendas


    def makePacket(self, merged_id, filenames_collection):
        # Set a custom timeout: 2 minutes.
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(120)

        merger = PdfFileMerger(strict=False)

        # if any('.ppt' in string for string in filenames_collection):
        for filename in filenames_collection:
            # Run this up to two times, in the event of a timeout, libreoffice RunTimeError ('Office probably died'), or other exception.
            attempts = 0
            while attempts < 2:
                try:
                    if filename.lower().endswith(('.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.rtf')):
                        call(['unoconv', '-f', 'pdf', filename])
                        path, keyword, exact_file = filename.partition('attachments/')
                        new_file = exact_file.split('.')[0] + '.pdf'
                        f = open(new_file, 'rb')
                        merger.append(PdfFileReader(f))
                        call(['rm', new_file])
                    else:
                        opened_url = urlopen(filename).read()
                        merger.append(BytesIO(opened_url), import_bookmarks=False)

                    if attempts >= 1:
                        LOGGER.info("Phew! It worked on the second try.")
                        LOGGER.info("\n")

                    break
                except Exception as err:
                    attempts += 1
                    LOGGER.info("\n")
                    LOGGER.info(("{} caused the following error: ").format(filename))
                    LOGGER.info(err)
                    if attempts < 2:
                        LOGGER.info(self.style.WARNING("Trying again...."))
                    else:
                        LOGGER.info(("Something went wrong. Please look at {}.").format(filename))
                        LOGGER.info("\n")
                except:
                    attempts += 1
                    LOGGER.info("\n")
                    LOGGER.info(("Unexpected error: {}").format(sys.exc_info()[0]))

        # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
        try:
            merger.write('merged_pdfs/' + merged_id + '.pdf')
            LOGGER.info(("Successful merge! {}").format(merged_id))
        except:
            LOGGER.info(("{0} caused the failure of writing {1} as a PDF").format(sys.exc_info()[0], merged_id))
            LOGGER.info(("We could not merge this file collection: {}").format(filenames_collection))

        # merger.write('merged_pdfs/' + merged_id + '.pdf')

        return merger

    def timeout_handler(self, signum, frame):
        raise Exception("ERROR: Timeout")

