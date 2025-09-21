from django import forms
from .models import SupportTicket, SupportTopic


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ('topic', 'subject', 'message', 'email', 'priority')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['email'].required = False
            self.fields['email'].initial = getattr(user, 'email', '')
