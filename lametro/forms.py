import requests

from django import forms

class AgendaUrlForm(forms.Form):

    agenda_url = forms.CharField(
        label='Agenda URL',
        max_length=500,
        error_messages={ 'required': 'Whoops! Please provide a valid URL.' },
        )

    def clean_agenda_url(self):
        agenda_url = self.cleaned_data['agenda_url']

        try:
          r = requests.head(agenda_url)
          if r.status_code == 200:
              return agenda_url
          elif r.status_code == 404:
              raise forms.ValidationError('Broken URL! Returns a 404.')
        except requests.exceptions.MissingSchema as e:
            raise forms.ValidationError('Not a valid URL! Check your link, and resubmit.')

class AgendaPdfForm(forms.Form):

      agenda_pdf = forms.FileField(
          label='Agenda PDF',
          error_messages={ 'required': 'Oh no! Please provide a valid PDF.'},
          )

      def clean_agenda_pdf(self):
          agenda_pdf = self.cleaned_data['agenda_pdf']

          if file_upload.name.lower().endswith('pdf'):
              return file_upload
          else:
              raise forms.ValidationError('File type not supported. Please submit a PDF.')