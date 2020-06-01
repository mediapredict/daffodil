# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.postgres.fields import HStoreField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunSQL("CREATE EXTENSION if not exists hstore;"),
        migrations.CreateModel(
            name='BasicHStoreData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hsdata', HStoreField()),
            ],
        ),
    ]
