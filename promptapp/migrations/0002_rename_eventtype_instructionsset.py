# Generated by Django 4.2.13 on 2024-05-20 06:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('promptapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='EventType',
            new_name='InstructionsSet',
        ),
    ]
