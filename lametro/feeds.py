from councilmatic_core.feeds import PersonDetailFeed

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
            recent_sponsored_bills = person.committee_sponsorships
        else:
            recent_sponsored_bills = []

        return recent_sponsored_bills
