from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apps.companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoadInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('external_load_id', models.CharField(max_length=64)),
                ('decision', models.CharField(max_length=32, choices=[('viewed', 'Viewed'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])),
                ('score', models.FloatField(null=True, blank=True)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='load_interactions', to='apps.companies.Company')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='load_interactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user'], name='activity_user_idx'), models.Index(fields=['company'], name='activity_company_idx'), models.Index(fields=['external_load_id'], name='activity_external_idx'), models.Index(fields=['decision'], name='activity_decision_idx')],
            },
        ),
        migrations.CreateModel(
            name='CommunicationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.CharField(max_length=32)),
                ('counterpart', models.CharField(blank=True, max_length=160)),
                ('summary', models.CharField(blank=True, max_length=255)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='communications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('status', models.CharField(default='open', max_length=32)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='support_tickets', to='apps.companies.Company')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='support_tickets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
