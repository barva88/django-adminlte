from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.exams.models import Subscription


class Command(BaseCommand):
    help = 'Grant initial 10 exam credits to all registered users (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument('--min-credits', type=int, default=10, help='Minimum credits to ensure per user')

    def handle(self, *args, **options):
        User = get_user_model()
        min_credits = options['min_credits']
        users = User.objects.all()
        total = users.count()
        self.stdout.write(f"Found {total} users. Ensuring each has at least {min_credits} credits.")

        updated = 0
        created = 0
        for user in users.iterator():
            sub, was_created = Subscription.objects.get_or_create(user=user, defaults={'status': 'active', 'credits_remaining': min_credits})
            if was_created:
                created += 1
                continue
            if sub.credits_remaining < min_credits:
                sub.credits_remaining = min_credits
                sub.save(update_fields=['credits_remaining'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Completed. Created: {created}, Updated: {updated} (out of {total})."))
