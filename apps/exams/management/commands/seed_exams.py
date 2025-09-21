from django.core.management.base import BaseCommand
from django.db import transaction
from apps.exams.models import Question, Choice, Exam, SubscriptionPlan
import random
from django.utils import timezone


CDL_CATEGORIES = [
    'General Knowledge', 'Air Brakes', 'Combination Vehicles', 'Hazardous Materials', 'Passenger', 'School Bus'
]
DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD']


def gen_question_text(idx, cat):
    return f"Sample question {idx} for {cat}: What is {idx} + {idx}?"


def gen_choice_text(idx, choice_no):
    return f"Answer option {choice_no} for Q{idx}"


class Command(BaseCommand):
    help = 'Seed exams data (idempotent). Creates questions and choices. --count controls total questions.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Target total number of questions to keep in DB')
        parser.add_argument('--create-exam', action='store_true', help='Create a "Sample Exam" record after seeding')

    def handle(self, *args, **options):
        count = options.get('count', 200)
        create_exam = options.get('create_exam', False)

        with transaction.atomic():
            # create plan if not exists
            SubscriptionPlan.objects.get_or_create(name='Basic', defaults={'price_cents': 999, 'period_months': 1, 'exam_credits': 50})

            # create some canonical exams (if desired)
            for slug in ['CDL General Knowledge', 'CDL Combination', 'CDL Air Brakes']:
                Exam.objects.get_or_create(title=slug, defaults={'category': slug})

            existing = Question.objects.count()
            to_create = max(0, count - existing)

            if to_create > 0:
                self.stdout.write(self.style.NOTICE(f'Creating {to_create} questions to reach {count} total...'))
                for i in range(existing + 1, existing + to_create + 1):
                    cat = random.choice(CDL_CATEGORIES)
                    diff = random.choices(DIFFICULTIES, weights=(50, 35, 15), k=1)[0]
                    q = Question.objects.create(
                        text=gen_question_text(i, cat),
                        category=cat,
                        difficulty=diff,
                        is_active=True,
                        created_at=timezone.now()
                    )
                    # create 2 choices only (one correct, one incorrect) to respect the unique_together constraint
                    correct_idx = random.choice([1, 2])
                    for ci in (1, 2):
                        Choice.objects.create(
                            question=q,
                            text=(str(i * 2) if ci == correct_idx else gen_choice_text(i, ci)),
                            is_correct=(ci == correct_idx)
                        )
                self.stdout.write(self.style.SUCCESS(f'Created {to_create} questions'))
            else:
                self.stdout.write(self.style.WARNING(f'Already have {existing} questions; nothing created.'))

            if create_exam:
                exam_title = 'Sample Exam'
                if Exam.objects.filter(title=exam_title).exists():
                    self.stdout.write(self.style.WARNING('Sample Exam already exists, skipping creation.'))
                else:
                    Exam.objects.create(title=exam_title, category='Sample', is_active=True)
                    self.stdout.write(self.style.SUCCESS('Created Sample Exam'))

        self.stdout.write(self.style.SUCCESS('Seeding complete'))
