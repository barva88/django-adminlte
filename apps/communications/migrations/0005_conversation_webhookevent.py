from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0004_commsynclog'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conversation_id', models.CharField(db_index=True, max_length=128, unique=True)),
                ('type', models.CharField(choices=[('chat', 'chat'), ('call', 'call')], db_index=True, max_length=8)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('transcript', models.TextField(blank=True, null=True)),
                ('recording_url', models.URLField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retell_conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-ended_at'],
                'indexes': [models.Index(fields=['user', 'ended_at'], name='communicati_user_id_ended_a1e0e8_idx')],
            },
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(db_index=True, max_length=128, unique=True)),
                ('provider', models.CharField(db_index=True, default='retell', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
