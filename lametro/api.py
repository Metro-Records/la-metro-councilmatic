import json

from django.conf import settings
from django.core import management
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, RedirectView

from haystack.query import SearchQuerySet

from lametro.models import LAMetroBill, LAMetroEvent, LAMetroSubject
from smartlogic.views import SmartLogicAPI


class PublicComment(RedirectView):
    '''
    Redirect to the public comment link for the current meeting. If there is
    more than one current meeting, or no current meetings, redirect to the
    generic public comment URL.
    '''
    def get_redirect_url(self, *args, **kwargs):
        current_meetings = LAMetroEvent.current_meeting()

        if current_meetings.count() == 1:
            return current_meetings.get().ecomment_url

        return LAMetroEvent.GENERIC_ECOMMENT_URL


@csrf_exempt
def refresh_guid_trigger(request, refresh_key):
    try:
        if refresh_key == settings.REFRESH_KEY:
            management.call_command('refresh_guid')
            return HttpResponse(200)
        else:
            print('You do not have the correct refresh_key to access this.')
    except AttributeError:
        print('You need a refresh_key in your local deployment settings files to access this.')
    return HttpResponse(403)


class LAMetroSmartLogicAPI(SmartLogicAPI):

    def get_queryset(self, *args, **kwargs):
        self.kwargs['endpoint'] = 'concepts'

        qs = super().get_queryset(*args, **kwargs)

        action = self.kwargs.get('action', 'suggest')

        if action not in ('suggest', 'relate'):
            raise ValueError('action must be one of: suggest, relate')

        if action == 'suggest':
            return self.get_suggestions(qs)

        else:
            return self.get_relations(qs)

    def get_suggestions(self, concepts):
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
                                if s['field']['name'].lower() == self.kwargs['term'].lower()
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

        return self.filter_concepts(suggestions)

    def get_relations(self, concepts):
        if int(concepts['total']) == 1:
            relations = {}

            if concepts['terms'][0]['term'].get('associated') and \
                    len(concepts['terms'][0]['term']['associated']) > 0:

                for field in concepts['terms'][0]['term']['associated']:
                    relations.update({
                        term['field']['id']: {'name': term['field']['name']}
                        for term in field['fields']
                    })

        else:
            relations = {
                term['term']['id']: {'name': term['term']['name']}
                for term in concepts['terms']
            }

        return self.filter_concepts(relations)

    def filter_concepts(self, concepts):
        guids = list(concepts.keys())
        subjects = list(LAMetroSubject.objects.filter(guid__in=guids, bill_count__gt=0)\
                                              .order_by('-bill_count')\
                                              .values('name', 'guid'))

        for subject in subjects:
            subject['display_name'] = subject['name'] + \
                concepts[subject['guid']].get('synonym_label', '')

        return {
            'status_code': 200,
            'concepts': concepts,
            'subjects': subjects,
        }


def fetch_object_counts(request, key):
    if settings.API_KEY == key:
        response = {
            'status_code': 200,
            'status': 'success',
            'bill_count': LAMetroBill.objects.count(),
            'event_count': LAMetroEvent.objects.count(),
            'search_index_count': SearchQuerySet().count()
        }
    else:
        response = {
            'status_code': 401,
            'status': 'unauthorized',
        }

    return JsonResponse(response)
