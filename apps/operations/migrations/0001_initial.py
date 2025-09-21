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
            name='Preference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('regions', models.JSONField(default=list, blank=True)),
                ('max_distance_miles', models.PositiveIntegerField(null=True, blank=True)),
                ('preferred_equipment', models.JSONField(default=list, blank=True)),
                ('availability', models.JSONField(default=dict, blank=True)),
                ('payment_pref', models.CharField(max_length=32, choices=[('factoring', 'Factoring'), ('quickpay', 'Quick Pay'), ('net30', 'Net 30')], default='net30')),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='preferences', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='preferences', to='apps.companies.Company')),
            ],
            options={
                'constraints': [models.CheckConstraint(check=models.Q(models.Q(user__isnull=False) | models.Q(company__isnull=False)), name='pref_user_or_company')],
                'indexes': [models.Index(fields=['user'], name='operations_user_idx'), models.Index(fields=['company'], name='operations_company_idx')],
            },
        ),
    ]
