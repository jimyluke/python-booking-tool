# Generated by Django 2.2 on 2021-08-17 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_ovenconsumption'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ovenconsumption',
            name='date_info',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
