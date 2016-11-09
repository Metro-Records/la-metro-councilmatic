from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.feedgenerator import Rss201rev2Feed
from django.conf import settings

from councilmatic_core.feeds import PersonDetailFeed
from councilmatic_core.models import Person

from lametro.models import LAMetroPerson

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
            recent_sponsored_bills = [
                s.bill for s in sorted(person.committee_sponsorships, key=lambda obj: obj.date, reverse=True)[:10]
            ]
        else:
            recent_sponsored_bills = []

        return recent_sponsored_bills
