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
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plan', models.CharField(max_length=32, choices=[('basic', 'Basic'), ('pro', 'Pro'), ('premium', 'Premium')])),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('credits', models.IntegerField(default=0)),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='subscriptions', to='apps.companies.Company')),
            ],
            options={
                'indexes': [models.Index(fields=['user'], name='memberships_user_idx'), models.Index(fields=['company'], name='memberships_company_idx'), models.Index(fields=['is_active'], name='memberships_active_idx')],
            },
        ),
        migrations.CreateModel(
            name='CreditLedger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('delta', models.IntegerField()),
                ('reason', models.CharField(blank=True, max_length=128)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('subscription', models.ForeignKey(on_delete=models.CASCADE, related_name='ledger', to='apps.memberships.Subscription')),
            ],
        ),
    ]
