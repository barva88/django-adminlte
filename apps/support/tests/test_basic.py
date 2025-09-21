from django.test import TestCase
from apps.support.models import SupportTopic, SupportTicket


class SupportBasicTests(TestCase):
    def test_create_topic_and_ticket(self):
        t = SupportTopic.objects.create(name='Test Topic')
        ticket = SupportTicket.objects.create(email='test@example.com', topic=t, subject='Hola', message='Ayuda')
        self.assertIn('Test Topic', str(t))
        self.assertTrue(ticket.pk)
