import urllib

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse

from haystack.query import SearchQuerySet

from councilmatic_core.feeds import PersonDetailFeed

from lametro.models import LAMetroBill, LAMetroPerson
from lametro.utils import to_datetime


class CouncilmaticFacetedSearchFeed(Feed):
    title_template = "feeds/search_item_title.html"
    description_template = "feeds/search_item_description.html"
    bill_model = LAMetroBill

    all_results = None
    sqs = (
        SearchQuerySet()
        .facet("bill_type")
        .facet("sponsorships", sort="index")
        .facet("controlling_body")
        .facet("inferred_status")
    )
    query = None

    def url_with_querystring(self, path, **kwargs):
        return path + "?" + urllib.parse.urlencode(kwargs)

    def get_object(self, request):
        self.queryDict = request.GET

        all_results = SearchQuerySet().all()
        facets = None

        if "selected_facets" in request.GET:
            facets = request.GET.getlist("selected_facets")

        if "q" in request.GET:
            self.query = request.GET["q"]
            results = all_results.filter(content=self.query)

            if facets:
                for facet in facets:
                    (facet_name, facet_value) = facet.split(":")
                    facet_name = facet_name.rsplit("_exact")[0]
                    results = results.narrow("%s:%s" % (facet_name, facet_value))
        elif facets:
            for facet in facets:
                (facet_name, facet_value) = facet.split(":")
                facet_name = facet_name.rsplit("_exact")[0]
                results = all_results.narrow("%s:%s" % (facet_name, facet_value))

        return results.order_by("-last_action_date")

    def title(self, obj):
        if self.query:
            title = (
                settings.SITE_META["site_name"]
                + ": Search for '"
                + self.query.capitalize()
                + "'"
            )
        else:
            title = settings.SITE_META["site_name"] + ": Filtered Search"

        return title

    def link(self, obj):
        url = self.url_with_querystring(
            reverse("{}:councilmatic_search_feed".format(settings.APP_NAME)),
            q=self.query,
        )
        return url

    def item_link(self, bill):
        return reverse("lametro:bill_detail", args=(bill.slug,))

    def item_pubdate(self, bill):
        return to_datetime(bill.last_action_date)

    def description(self, obj):
        return "Bills returned from search"

    def items(self, query):
        l_items = query[:20]
        pks = [i.pk for i in l_items]
        bills = self.bill_model.objects.filter(pk__in=pks).order_by("-last_action_date")
        return bills


class LAMetroPersonDetailFeed(PersonDetailFeed):
    """The PersonDetailFeed provides an RSS feed for a given committee member,
    returning the most recent 20 bills for which they are the primary sponsor;
    and for each bill, the list of sponsores and the action history.
    """

    model = LAMetroPerson

    def get_object(self, request, slug):
        o = LAMetroPerson.objects.get(slug=slug)

        return o

    def items(self, person):
        person.committee_sponsorships

        if person.committee_sponsorships:
            recent_sponsored_bills = person.committee_sponsorships
        else:
            recent_sponsored_bills = []

        return recent_sponsored_bills
