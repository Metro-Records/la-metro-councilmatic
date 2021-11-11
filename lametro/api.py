import json

from django.conf import settings
from django.core import management
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, RedirectView

from haystack.query import SearchQuerySet

from lametro.models import LAMetroBill, LAMetroEvent, LAMetroSubject


class PublicComment(RedirectView):
    """
    Redirect to the public comment link for the current meeting. If there is
    more than one current meeting, or no current meetings, redirect to the
    generic public comment URL.
    """

    def get_redirect_url(self, *args, **kwargs):
        current_meetings = LAMetroEvent.current_meeting()

        if current_meetings.count() == 1:
            return current_meetings.get().ecomment_url

        return LAMetroEvent.GENERIC_ECOMMENT_URL


@csrf_exempt
def refresh_guid_trigger(request, refresh_key):
    try:
        if refresh_key == settings.REFRESH_KEY:
            management.call_command("refresh_guid")
            return HttpResponse(200)
        else:
            print("You do not have the correct refresh_key to access this.")
    except AttributeError:
        print(
            "You need a refresh_key in your local deployment settings files to access this."
        )
    return HttpResponse(403)


def fetch_subjects(request):
    from smartlogic.client import SmartLogic

    s = SmartLogic(settings.SMART_LOGIC_KEY, token=request.GET.get('token', None))

    query_parameters = request.GET.dict()
    search_term = query_parameters.pop('term')

    concepts = s.concepts(search_term, query_parameters)

    suggestions = {}

    if concepts.get('terms'):
        for result in concepts['terms']:
            term = result['term']
            synonym_label = ''

            if term.get('equivalence') and len(term['equivalence']) > 0:
                for equivalent_term in term['equivalence']:
                    try:
                        synonym = [
                            s['field']['name'] for s in equivalent_term['fields']
                            if s['field']['name'].lower() == search_term.lower()
                        ][0]
                    except IndexError:
                        continue
                    else:
                        synonym_label = ' ({})'.format(synonym)
                        break

            suggestions[term['id']] = {
                'name': term['name'],
                'synonym_label': synonym_label,
            }

    guids = list(suggestions.keys())
    subjects = list(LAMetroSubject.objects.filter(guid__in=guids, bill_count__gt=0)\
                                          .order_by('-bill_count')\
                                          .values('name', 'guid'))

    for subject in subjects:
        subject['display_name'] = subject['name'] + suggestions[subject['guid']]['synonym_label']

    response = {
        'status_code': 200,
        'guids': guids,
        'subjects': subjects,
    }

    return JsonResponse(response)


def fetch_object_counts(request, key):
    if settings.API_KEY == key:
        response = {
            "status_code": 200,
            "status": "success",
            "bill_count": LAMetroBill.objects.count(),
            "event_count": LAMetroEvent.objects.count(),
            "search_index_count": SearchQuerySet().count(),
        }
    else:
        response = {
            "status_code": 401,
            "status": "unauthorized",
        }

    return JsonResponse(response)
