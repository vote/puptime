# Generated by Django 3.1.5 on 2021-01-13 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uptime', '0003_auto_20210113_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='check',
            name='status',
            field=models.TextField(choices=[('UP', 'up'), ('DOWN', 'down'), ('BLOCKED', 'blocked')], null=True),
        ),
    ]
