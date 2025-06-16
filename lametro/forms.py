from captcha.fields import ReCaptchaField
from captcha.fields import ReCaptchaV3
from haystack.backends import SQ
from haystack.inputs import Raw
from haystack.query import EmptySearchQuerySet

from councilmatic_core.views import CouncilmaticSearchForm


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
        reserved_characters = "|&*/\!{[]}~-+'()^:"  # noqa
        mapping = {char: f"\{char}" for char in reserved_characters}  # noqa
        table = str.maketrans(mapping)
        q = q.translate(table)

        # Downcase boolean operators
        for op in ("OR", "AND"):
            q = q.replace(op, op.lower())

        return q

    def _full_text_search(self, sqs):
        report_filter = SQ()
        attachment_filter = SQ()

        for token in self.cleaned_data["q"].split(" and "):
            report_filter &= SQ(text=Raw(token))
            attachment_filter &= SQ(attachment_text=Raw(token))

        sqs = sqs.filter(report_filter)

        if self.search_corpus == "all":
            sqs = sqs.filter_or(attachment_filter)

        return sqs

    def _topic_search(self, sqs):
        terms = [
            term.strip().replace('"', "")
            for term in self.cleaned_data["q"].split(" and ")
            if term
        ]

        topic_filter = SQ()
        for term in terms:
            topic_filter &= (
                SQ(topics__in=[term])
                | SQ(bill_type__in=[term])
                | SQ(lines_and_ways__in=[term])
                | SQ(phase__in=[term])
                | SQ(project__in=[term])
                | SQ(metro_location__in=[term])
                | SQ(geo_admin_location__in=[term])
                | SQ(significant_date__in=[term])
                | SQ(motion_by__in=[term])
                | SQ(plan_program_policy__in=[term])
            )

        sqs = sqs.filter(topic_filter)

        return sqs

    def search(self):
        if not self.is_valid():
            return EmptySearchQuerySet()

        sqs = super(LAMetroCouncilmaticSearchForm, self).search()

        has_query = hasattr(self, "cleaned_data") and self.cleaned_data["q"]

        if has_query:
            if self.result_type == "keyword":
                sqs = self._full_text_search(sqs)
            elif self.result_type == "topic":
                sqs = self._topic_search(sqs)
            else:
                # Combine full text and tag search results
                sqs = self._full_text_search(sqs) | self._topic_search(sqs)

        return sqs
