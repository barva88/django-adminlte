from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('apps.companies', '0001_initial'),
        ('apps.drivers', '0001_initial'),
        ('apps.vehicles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doc_type', models.CharField(max_length=32, choices=[('w9', 'IRS W-9'), ('mc_dot_letter', 'MC/DOT Letter'), ('medical_card', 'Medical Card'), ('insurance', 'Insurance'), ('other', 'Other')])),
                ('title', models.CharField(blank=True, max_length=160)),
                ('file', models.FileField(upload_to='docs/%Y/%m/')),
                ('issued_date', models.DateField(null=True, blank=True)),
                ('expiry_date', models.DateField(null=True, blank=True)),
                ('meta', models.JSONField(default=dict, blank=True)),
                ('company', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='documents', to='apps.companies.Company')),
                ('driver', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='documents', to='apps.drivers.Driver')),
                ('vehicle', models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, related_name='documents', to='apps.vehicles.Vehicle')),
            ],
            options={
                'indexes': [models.Index(fields=['company'], name='documents_company_idx'), models.Index(fields=['driver'], name='documents_driver_idx'), models.Index(fields=['vehicle'], name='documents_vehicle_idx'), models.Index(fields=['doc_type'], name='documents_doc_type_idx')],
            },
        ),
    ]
