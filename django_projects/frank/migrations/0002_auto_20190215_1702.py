# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from frank.management.commands import populate_parameters

class Migration(migrations.Migration):

    dependencies = [
        ('frank', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_parameters.populate),
    ]
