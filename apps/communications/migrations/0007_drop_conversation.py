from django.db import migrations

class Migration(migrations.Migration):
    # Merge the two 0006 branches then drop model if it still exists.
    dependencies = [
        ('communications', '0006_conversationmemory_and_more'),
        ('communications', '0006_drop_conversation'),
    ]

    operations = [
        migrations.DeleteModel(name='Conversation'),
    ]
