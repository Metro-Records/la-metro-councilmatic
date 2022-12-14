import requests

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q

from captcha.fields import ReCaptchaField
from captcha.fields import ReCaptchaV3
from haystack.backends import SQ
from haystack.inputs import Raw
from haystack.query import EmptySearchQuerySet

from councilmatic_core.views import CouncilmaticSearchForm

from lametro.models import LAMetroBill, LAMetroPerson


class LAMetroCouncilmaticSearchForm(CouncilmaticSearchForm):

    captcha = ReCaptchaField(widget=ReCaptchaV3)

    def __init__(self, *args, **kwargs):
        if kwargs.get("search_corpus"):
            self.search_corpus = kwargs.pop("search_corpus")

        self.result_type = kwargs.pop("result_type", None)

        super(LAMetroCouncilmaticSearchForm, self).__init__(*args, **kwargs)

    def clean_q(self):
        q = self.cleaned_data["q"]

        # Close open quotes
        if q.count('"') % 2:
            q += '"'

        # Escape reserved characters
        reserved_characters = r"""|&*/\!{[]}~-+'()^:"""

        for char in reserved_characters:
            q = q.replace(char, r"\{}".format(char))

        # Downcase boolean operators
        for op in ("OR", "AND"):
            q = q.replace(op, op.lower())

        return q

    def _full_text_search(self, sqs):
        report_filter = SQ()
        attachment_filter = SQ()

        for token in self.cleaned_data["q"].split(" AND "):
            report_filter &= SQ(text=Raw(token))
            attachment_filter &= SQ(attachment_text=Raw(token))

        sqs = sqs.filter(report_filter)

        if self.search_corpus == "all":
            sqs = sqs.filter_or(attachment_filter)

        return sqs

    def _topic_search(self, sqs):
        terms = [
            term.strip().replace('"', "")
            for term in self.cleaned_data["q"].split(" AND ")
            if term
        ]

        topic_filter = Q()

        for term in terms:
            topic_filter |= Q(subject__icontains=term)

        tagged_results = LAMetroBill.objects.filter(topic_filter).values_list(
            "id", flat=True
        )

        if self.result_type == "keyword":
            sqs = sqs.exclude(id__in=tagged_results)

        elif self.result_type == "topic":
            sqs = sqs.filter(id__in=tagged_results)

        return sqs

    def search(self):
        if not self.is_valid():
            return EmptySearchQuerySet()

        sqs = super(LAMetroCouncilmaticSearchForm, self).search()

        has_query = hasattr(self, "cleaned_data") and self.cleaned_data["q"]

        if has_query:
            sqs = self._full_text_search(sqs)
            sqs = self._topic_search(sqs)

        return sqs


class AgendaUrlForm(forms.Form):

    agenda = forms.CharField(
        label="Agenda URL",
        max_length=500,
        error_messages={"required": "Whoops! Please provide a valid URL."},
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter URL...",
                "id": "agenda_url",
            }
        ),
    )

    def clean_agenda(self):
        agenda_url = self.cleaned_data["agenda"]

        try:
            r = requests.head(agenda_url)
            if r.status_code == 200:
                return agenda_url
            elif r.status_code == 404:
                raise forms.ValidationError("Broken URL! Returns a 404.")
        except requests.exceptions.MissingSchema:
            raise forms.ValidationError(
                "Not a valid URL! Check your link, and resubmit."
            )


class AgendaPdfForm(forms.Form):

    agenda = forms.FileField(
        label="Agenda PDF",
        error_messages={"required": "Oh no! Please provide a valid PDF."},
        widget=forms.FileInput(
            attrs={"id": "pdf-form-input", "onchange": "previewPDF(this);"}
        ),
    )

    def clean_agenda(self):
        agenda_pdf = self.cleaned_data["agenda"]

        if isinstance(
            agenda_pdf, InMemoryUploadedFile
        ) and agenda_pdf.name.lower().endswith("pdf"):
            return agenda_pdf
        else:
            raise forms.ValidationError("File type not supported. Please submit a PDF.")


class PersonHeadshotForm(forms.Form):

    headshot = forms.FileField(
            label='Headshot File',
            error_messages={'required': 'Oops! Please provide a valid image file.'},
            widget=forms.FileInput(attrs={'id':'headshot-form-input'})
        )

    headshot_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)


class PersonBioForm(forms.ModelForm): # can change this to just forms.Form if getting weird

    # bio = forms.CharField(
    #         label='Bio',
    #         error_messages={ 'required': 'Whoops! Please provide a bio.' },
    #         widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Enter bio', 'id': 'bio'})
    #     )

    bio_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    class Meta:
        model = LAMetroPerson
        fields = ['biography']

