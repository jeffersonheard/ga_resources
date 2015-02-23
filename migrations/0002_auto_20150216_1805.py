# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import timedelta.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ga_resources', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataresource',
            name='refresh_every',
            field=timedelta.fields.TimedeltaField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
