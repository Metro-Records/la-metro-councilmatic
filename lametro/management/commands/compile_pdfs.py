import sqlalchemy as sa
from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import StringIO, BytesIO

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

        # for idx, el in enumerate(report_packet_raw):
        #     try:
        #       self.makePacket(el[1])
        #     except:
        #       self.stdout.write(self.style.ERROR("Did not compile PDFs at index {0} for bill {1}").format(idx, el[0]))
        #       pass

        self.stdout.write(self.style.NOTICE("Finding all documents for event agendas."))
        self.stdout.write(self.style.NOTICE(".........."))
        event_packet_raw = self.findEventAgendaPacket()

        # for idx, el in enumerate(event_packet_raw):
        #     try:
        #       self.makePacket(el[1])
        #     except:
        #       self.stdout.write(self.style.ERROR("Did not compile PDFs at index {0} for event {1}").format(idx, el[0]))
        #       pass

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


    def makePacket(self, filenames_collection):

      merger = PdfFileMerger()

      for filename in filenames_collection:
          opened_url = urlopen(filename).read()
          merger.append(BytesIO(opened_url), 'rb')

      # This is a PdfFileMerger object, which can be written to a new file like so:
      # merger.write("document-output.pdf")

      return merger


