from django.db import migrations

class Migration(migrations.Migration):
    # Mark as applied/empty; keep same number but depend on previous 0005 so Django can consider both 0006 variants.
    dependencies = [
        ('communications', '0005_conversation_webhookevent'),
    ]

    # No operations; acts as an alternative branch that will be merged by 0007
    operations = []
