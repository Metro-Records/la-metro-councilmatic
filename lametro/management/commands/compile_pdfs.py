import sqlalchemy as sa

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
        self.findBoardReportPacket()

        self.stdout.write(self.style.NOTICE("Finding all documents for event agendas."))
        self.stdout.write(self.style.NOTICE(".........."))
        self.findEventAgendaPacket()

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
        for document in board_reports:
            print(document)


    def findEventAgendaPacket(self):

        query = '''
        SELECT i.event_id, array_agg(distinct d.url)
        FROM councilmatic_core_billdocument AS d
        INNER JOIN councilmatic_core_eventagendaitem as i
        ON i.bill_id=d.bill_id
        GROUP BY i.event_id;
        '''

        event_agendas = self.connection.execute(sa.text(query))

        # Testing
        for document in event_agendas:
            print(document)


