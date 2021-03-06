# Generated by Django 3.1.5 on 2021-01-14 18:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Check',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.TextField(choices=[('UP', 'up'), ('DOWN', 'down'), ('BLOCKED', 'blocked')], null=True)),
                ('up', models.BooleanField(null=True)),
                ('blocked', models.BooleanField(null=True)),
                ('ignore', models.BooleanField(null=True)),
                ('load_time', models.FloatField(null=True)),
                ('error', models.TextField(null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('content', models.TextField(null=True)),
                ('snapshot_url', models.TextField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Downtime',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_down_check', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='downtime_first', to='uptime.check')),
                ('last_down_check', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='downtime_last', to='uptime.check')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Proxy',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.TextField(null=True)),
                ('address', models.TextField(null=True)),
                ('description', models.TextField(null=True)),
                ('status', models.TextField(choices=[('CREATING', 'creating'), ('PREPARING', 'preparing'), ('UP', 'up'), ('BURNED', 'burned'), ('DOWN', 'down')], null=True)),
                ('failure_count', models.IntegerField(null=True)),
                ('last_used', models.DateTimeField(null=True)),
                ('metadata', models.JSONField(null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.TextField(null=True)),
                ('active', models.BooleanField(default=True)),
                ('description', models.TextField(null=True)),
                ('metadata', models.JSONField(null=True)),
                ('status', models.TextField(choices=[('UP', 'up'), ('DOWN', 'down'), ('BLOCKED', 'blocked')], null=True)),
                ('status_changed_at', models.DateTimeField(null=True)),
                ('uptime_day', models.FloatField(null=True)),
                ('uptime_week', models.FloatField(null=True)),
                ('uptime_month', models.FloatField(null=True)),
                ('uptime_quarter', models.FloatField(null=True)),
                ('last_downtime', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='site_last', to='uptime.downtime')),
                ('last_went_blocked_check', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='site_blocked', to='uptime.check')),
                ('last_went_unblocked_check', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='site_unblocked', to='uptime.check')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-modified_at'],
            },
        ),
        migrations.AddField(
            model_name='downtime',
            name='site',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='uptime.site'),
        ),
        migrations.AddField(
            model_name='downtime',
            name='up_check',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='downtime_up', to='uptime.check'),
        ),
        migrations.AddField(
            model_name='check',
            name='content',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='uptime.content'),
        ),
        migrations.AddField(
            model_name='check',
            name='proxy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='uptime.proxy'),
        ),
        migrations.AddField(
            model_name='check',
            name='site',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='uptime.site'),
        ),
    ]
