from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('apps.companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('make', models.CharField(max_length=64)),
                ('model', models.CharField(max_length=64)),
                ('year', models.PositiveIntegerField()),
                ('equipment_type', models.CharField(max_length=32, choices=[('dry_van', 'Dry Van'), ('reefer', 'Reefer'), ('flatbed', 'Flatbed'), ('stepdeck', 'Stepdeck'), ('power_only', 'Power Only')])),
                ('vin', models.CharField(blank=True, max_length=32)),
                ('plate', models.CharField(blank=True, max_length=32)),
                ('gvwr', models.PositiveIntegerField(null=True, blank=True)),
                ('insurance_policy', models.CharField(blank=True, max_length=64)),
                ('insurance_exp', models.DateField(null=True, blank=True)),
                ('company', models.ForeignKey(on_delete=models.CASCADE, related_name='vehicles', to='apps.companies.Company')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=['company', 'vin'], name='unique_company_vin')],
                'indexes': [models.Index(fields=['company'], name='vehicles_company_idx'), models.Index(fields=['vin'], name='vehicles_vin_idx'), models.Index(fields=['plate'], name='vehicles_plate_idx')],
            },
        ),
    ]
