import sqlalchemy as sa
from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import StringIO, BytesIO
from subprocess import call
import signal
import sys

from django.core.management.base import BaseCommand
from django.conf import settings

DB_CONN = 'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'

ENGINE = sa.create_engine(DB_CONN.format(**settings.DATABASES['default']),
                          convert_unicode=True,
                          server_side_cursors=True)

class Command(BaseCommand):
    help = "This command compiles PDFs for the LA Metro Agenda and Board Report packets."


    def handle(self, *args, **options):

        self.connection = ENGINE.connect()

        self.stdout.write(self.style.NOTICE("Finding all documents for board reports."))
        self.stdout.write(self.style.NOTICE(".........."))
        report_packet_raw = self.findBoardReportPacket()

        for idx, el in enumerate(report_packet_raw):
            board_report_id = el[0]
            filenames = el[1]
            self.makePacket(board_report_id, filenames)

        self.stdout.write(self.style.NOTICE("Finding all documents for event agendas."))
        self.stdout.write(self.style.NOTICE(".........."))
        event_packet_raw = self.findEventAgendaPacket()

        for idx, el in enumerate(event_packet_raw):
            event_id = el[0]
            filenames = el[1]
            self.makePacket(event_id, filenames)

        self.stdout.write(self.style.SUCCESS(".........."))
        self.stdout.write(self.style.SUCCESS("Job complete. Excellent work, everyone."))


    def findBoardReportPacket(self):

        query = '''
        SELECT bill_id, array_agg(url) as url
        FROM councilmatic_core_billdocument
        GROUP BY bill_id
        '''
        board_reports = self.connection.execute(sa.text(query))

        # Testing
        # for document in board_reports:
        #     print(document)

        return board_reports


    def findEventAgendaPacket(self):
        # If we want to include the note in a nested array: SELECT i.event_id, array_agg(array[d.note, d.url])
        query = '''
        SELECT i.event_id, array_agg(DISTINCT d.url)
        FROM councilmatic_core_billdocument AS d
        INNER JOIN councilmatic_core_eventagendaitem as i
        ON i.bill_id=d.bill_id
        GROUP BY i.event_id;
        '''

        event_agendas = self.connection.execute(sa.text(query))

        # Testing
        # for document in event_agendas:
        #     print(document)

        return event_agendas


    def makePacket(self, merged_id, filenames_collection):
        # Set a custom timeout: 2 minutes.
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(120)

        merger = PdfFileMerger()

        for filename in filenames_collection:
            print(filename)
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
                    break
                except Exception as err:
                    attempts += 1
                    self.stdout.write(self.style.NOTICE(err))
                    if attempts < 3:
                        self.stdout.write(self.style.NOTICE("Trying {}, again. Do not worry: they're good dogs Brent.").format(filename))
                    else:
                        self.stdout.write(self.style.NOTICE("Something went wrong. Please look at {}.").format(filename))
                except:
                    attempts += 1
                    self.stdout.write(self.style.NOTICE("Unexpected error: {}").format(sys.exc_info()[0]))


        # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
        try:
            merger.write('merged_pdfs/' + merged_id + '.pdf')
        except:
            self.stdout.write(self.style.NOTICE("{0} caused the failure of writing {1} as a PDF".format(sys.exc_info()[0], merged_id)))

        return merger

    def timeout_handler(self, signum, frame):
        raise Exception("ERROR: Timeout")

