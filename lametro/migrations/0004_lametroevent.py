# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-11-28 15:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('councilmatic_core', '0027_merge'),
        ('lametro', '0003_lametroperson'),
    ]

    operations = [
        migrations.CreateModel(
            name='LAMetroEvent',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('councilmatic_core.event',),
        ),
    ]