# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-04 10:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maxlead_site', '0009_reviews_image_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviews',
            name='content',
            field=models.TextField(default='', null=True, verbose_name='Content'),
        ),
    ]
