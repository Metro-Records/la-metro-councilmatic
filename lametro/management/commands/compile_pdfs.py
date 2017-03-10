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
        self.compileBoardReportPacket()

        self.stdout.write(self.style.NOTICE("Finding all documents for event agendas."))
        self.stdout.write(self.style.NOTICE(".........."))
        self.compileEventAgendaPacket()

        self.stdout.write(self.style.SUCCESS(".........."))
        self.stdout.write(self.style.SUCCESS("Job complete. Excellent work, everyone."))


    def findBoardReportPacket(self):

        query = '''
        SELECT bill_id, array_agg(url) as url
        FROM councilmatic_core_billdocument
        GROUP BY bill_id
        '''
        board_reports = self.connection.execute(sa.text(query))


    def findEventAgendaPacket(self):

        # query = '''
        # SELECT array_agg(distinct d.url), d.bill_id, a.date, a.organization_id
        # FROM councilmatic_core_billdocument AS d
        # INNER JOIN councilmatic_core_action AS a
        # ON d.bill_id=a.bill_id where d.bill_id='ocd-bill/0e886916-deef-4f59-9e66-914bb1b5593a'
        # GROUP BY d.bill_id, a.date, a.organization_id;
        # '''

        query = '''
        SELECT i.event_id, array_agg(distinct d.url)
        FROM councilmatic_core_billdocument AS d
        INNER JOIN councilmatic_core_eventagendaitem as i
        ON i.bill_id=d.bill_id
        WHERE i.event_id='ocd-event/e7896758-23bb-42fe-93db-8231cd8604d1'
        GROUP BY i.event_id;
        '''

        event_agendas = self.connection.execute(sa.text(query))

