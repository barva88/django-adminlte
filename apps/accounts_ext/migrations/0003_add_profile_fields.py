from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts_ext", "0002_rename_accounts_ext_user_idx_accounts_ex_user_id_66573c_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_image',
            field=models.ImageField(upload_to='profiles/', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='city',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='state',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='country',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='zip_code',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='company_name',
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='dot_number',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='mc_number',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='preferred_language',
            field=models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('es', 'Español')]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='timezone',
            field=models.CharField(max_length=50, default='UTC'),
        ),
    ]
