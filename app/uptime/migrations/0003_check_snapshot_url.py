# Generated by Django 3.1.5 on 2021-01-11 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uptime', '0002_site_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='check',
            name='snapshot_url',
            field=models.TextField(null=True),
        ),
    ]