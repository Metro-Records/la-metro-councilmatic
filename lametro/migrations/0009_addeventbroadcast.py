# Generated by Django 2.2.25 on 2022-04-01 21:06
from datetime import datetime

from django.db import migrations, models
import django.db.models.deletion

from lametro.models import app_timezone


def create_event_broadcast(apps, schema_editor):
    Event = apps.get_model('councilmatic_core', 'Event')
    EventBroadcast = apps.get_model('lametro', 'EventBroadcast')
    past_events = Event.objects.filter(
        event__start_date__lte=app_timezone.localize(datetime.now()).isoformat()
    )
    for event in past_events:
        EventBroadcast.objects.create(event_id=event.event_id, observed=True)


def delete_event_broadcast(apps, schema_editor):
    EventBroadcast = apps.get_model('lametro', 'EventBroadcast')
    EventBroadcast.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lametro', '0008_add_has_broadcast_to_extras'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventBroadcast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observed', models.BooleanField(default=False)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='broadcast', to='lametro.LAMetroEvent')),
            ],
        ),
        migrations.RunPython(create_event_broadcast, delete_event_broadcast),
    ]