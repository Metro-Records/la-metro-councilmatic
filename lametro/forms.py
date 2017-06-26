from django import forms

class AgendaUrlForm(forms.Form):

    agenda_url = forms.CharField(
        label='Agenda URL',
        max_length=500,
        # widget=forms.TextInput(attrs={'class': "form-control", 'id':'highSchool', 'placeholder': 'Start typing...'}),
        error_messages={ 'required': 'Whoops! Please provide a URL.' },
        )