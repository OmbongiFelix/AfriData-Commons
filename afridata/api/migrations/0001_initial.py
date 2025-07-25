# Generated by Django 5.2.2 on 2025-07-10 18:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Human-readable name for this API key', max_length=100)),
                ('key', models.CharField(editable=False, max_length=64, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='APIUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.CharField(max_length=200)),
                ('method', models.CharField(max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('response_code', models.IntegerField()),
                ('response_time', models.FloatField(help_text='Response time in milliseconds')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('api_key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to='api.apikey')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['api_key', 'timestamp'], name='api_apiusag_api_key_f9d4f8_idx'), models.Index(fields=['endpoint', 'timestamp'], name='api_apiusag_endpoin_2fdec3_idx')],
            },
        ),
    ]


