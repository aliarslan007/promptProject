# Generated by Django 4.2.13 on 2024-05-26 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promptapp', '0005_remove_instructionsset_instructiona_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='settingpage',
            name='Claude_API_status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='settingpage',
            name='OpenAI_API_status',
            field=models.BooleanField(default=False),
        ),
    ]
