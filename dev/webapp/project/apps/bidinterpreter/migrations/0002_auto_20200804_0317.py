# Generated by Django 2.2.4 on 2020-08-04 03:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bidinterpreter', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='biddoc',
            old_name='bid',
            new_name='deal',
        ),
    ]
