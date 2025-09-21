from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('dot', models.CharField(blank=True, max_length=32)),
                ('mc', models.CharField(blank=True, max_length=32)),
                ('ein', models.CharField(blank=True, max_length=32)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('company_type', models.CharField(max_length=32, choices=[('owner_operator', 'Owner-Operator'), ('small_fleet', 'Small Fleet'), ('dispatcher', 'Dispatcher')])),
                ('fleet_size', models.PositiveIntegerField(default=1)),
                ('notes', models.TextField(blank=True)),
                ('owner', models.ForeignKey(on_delete=models.PROTECT, related_name='owned_companies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=['owner', 'name'], name='unique_owner_company_name')],
                'indexes': [models.Index(fields=['owner'], name='companies_owner_idx'), models.Index(fields=['dot'], name='companies_dot_idx'), models.Index(fields=['mc'], name='companies_mc_idx')],
            },
        ),
    ]
