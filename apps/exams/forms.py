from django import forms


class StartExamForm(forms.Form):
    confirm = forms.BooleanField(required=True)


class AnswerForm(forms.Form):
    choice_id = forms.IntegerField(required=False)
    # For true/false questions, use choice mapping where choice may be null
