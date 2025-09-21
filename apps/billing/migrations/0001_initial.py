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
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number', models.CharField(max_length=32, unique=True)),
                ('amount_cents', models.PositiveIntegerField()),
                ('currency', models.CharField(default='USD', max_length=8)),
                ('status', models.CharField(default='open', max_length=32, choices=[('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid'), ('void', 'Void')])),
                ('due_date', models.DateField(null=True, blank=True)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices', to='apps.companies.Company')),
            ],
            options={
                'indexes': [models.Index(fields=['company'], name='billing_company_idx'), models.Index(fields=['status'], name='billing_status_idx')],
            },
        ),
    ]
