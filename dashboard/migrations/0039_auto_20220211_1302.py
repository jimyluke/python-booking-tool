# Generated by Django 2.2 on 2022-02-11 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0038_auto_20220211_1118'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AlloyingElement',
        ),
        migrations.DeleteModel(
            name='AlloyStandard',
        ),
        migrations.DeleteModel(
            name='Chip',
        ),
        migrations.DeleteModel(
            name='ChipInfo',
        ),
        migrations.DeleteModel(
            name='GasConsumption',
        ),
        migrations.DeleteModel(
            name='Scrap',
        ),
        migrations.AlterField(
            model_name='csvfilesdata',
            name='Voltage4',
            field=models.FloatField(default=0, null=True),
        ),
    ]
