from django import forms


class FaqSearchForm(forms.Form):
    q = forms.CharField(required=False, max_length=255, label='Buscar')
