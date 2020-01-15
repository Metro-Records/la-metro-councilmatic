from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from opencivicdata.legislative.models import Bill
from lametro.models import LAMetroSubject


@receiver(post_save, sender=Bill)
def create_lametro_subject(sender, instance, created, **kwargs):
    '''
    Create LAMetroSubject instances for each subject on an incoming bill. There
    is a unique constraint on subject name - ignore violations so we can bulk
    create subjects without querying for or introducing duplicates.

    Create subjects on both create *and* update, because updates may include
    new subjects.
    '''
    LAMetroSubject.objects.bulk_create([
        LAMetroSubject(name=s) for s in instance.subject
    ], ignore_conflicts=True)


@receiver(pre_delete, sender=Bill)
def destroy_lametro_subject(sender, instance, using, **kwargs):
    '''
    When a bill is deleted, remove LAMetroSubject instances for subjects that
    are not associated with any remaining bills.
    '''
    to_delete = []

    for s in bill.subject:
        if not Bill.objects.filter(subject__contains=[s]).exists():
            to_delete.append(s)

    if len(to_delete) > 0:
        LAMetroSubject.objects.filter(name__in=to_delete).delete()
