# Generated by Django 2.0.6 on 2018-07-17 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maxlead_site', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='stocks_role',
            field=models.CharField(max_length=50, verbose_name='Stocks Role'),
        ),
    ]