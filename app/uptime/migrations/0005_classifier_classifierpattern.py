# Generated by Django 3.1.4 on 2020-12-18 17:14

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('uptime', '0004_auto_20201217_2122'),
    ]

    operations = [
        migrations.CreateModel(
            name='Classifier',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ClassifierPattern',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pattern_type', models.TextField(choices=[('BODY_REQUIRED', 'body_required'), ('TITLE_DOWN', 'title_down'), ('BODY_DOWN', 'body_down'), ('BODY_BLOCKED', 'body_blocked')])),
                ('pattern', models.TextField()),
                ('classifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uptime.classifier')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
