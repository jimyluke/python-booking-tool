# Generated by Django 2.2 on 2021-09-10 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0013_auto_20210910_1446'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OvenConsumption',
            new_name='GasConsumption',
        ),
    ]
