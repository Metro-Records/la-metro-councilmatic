import requests

from django import forms

class AgendaUrlForm(forms.Form):

    agenda = forms.CharField(
        label='Agenda URL',
        max_length=500,
        error_messages={ 'required': 'Whoops! Please provide a valid URL.' },
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter URL...', 'id': 'agenda_url'}),
        )

    def clean_agenda(self):
        agenda_url = self.cleaned_data['agenda']

        try:
          r = requests.head(agenda_url)
          if r.status_code == 200:
              return agenda_url
          elif r.status_code == 404:
              raise forms.ValidationError('Broken URL! Returns a 404.')
        except requests.exceptions.MissingSchema as e:
            raise forms.ValidationError('Not a valid URL! Check your link, and resubmit.')

class AgendaPdfForm(forms.Form):

      agenda = forms.FileField(
          label='Agenda PDF',
          error_messages={ 'required': 'Oh no! Please provide a valid PDF.'},
          widget=forms.FileInput(attrs={'id':'pdf-form-input', 'onchange':'previewPDF(this);'}),
          )

      def clean_agenda(self):
          agenda_pdf = self.cleaned_data['agenda']

          print("cleaning...", agenda_pdf.name.lower())

          if agenda_pdf.name.lower().endswith('pdf'):
              return agenda_pdf
          else:
              raise forms.ValidationError('File type not supported. Please submit a PDF.')