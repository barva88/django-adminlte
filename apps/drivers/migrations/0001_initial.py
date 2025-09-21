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
            name='Driver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cdl_number', models.CharField(max_length=64)),
                ('cdl_class', models.CharField(max_length=4, choices=[('A', 'Class A'), ('B', 'Class B'), ('C', 'Class C')])),
                ('experience_years', models.PositiveIntegerField(default=0)),
                ('medical_card_exp', models.DateField(null=True, blank=True)),
                ('endorsements', models.JSONField(default=list, blank=True)),
                ('company', models.ForeignKey(on_delete=models.CASCADE, related_name='drivers', to='apps.companies.Company')),
                ('user', models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='drivers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=['company', 'cdl_number'], name='unique_company_cdl')],
                'indexes': [models.Index(fields=['company'], name='drivers_company_idx'), models.Index(fields=['cdl_number'], name='drivers_cdl_idx')],
            },
        ),
    ]
