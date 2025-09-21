from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('role', models.CharField(choices=[('carrier', 'Carrier'), ('driver', 'Driver'), ('dispatcher', 'Dispatcher'), ('admin', 'Admin')], default='carrier', max_length=32)),
                ('is_company_admin', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='truck_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user'], name='accounts_ext_user_idx')],
            },
        ),
    ]
