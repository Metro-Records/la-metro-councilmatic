import json

from django.conf import settings
from django.core import management
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, RedirectView

from haystack.query import SearchQuerySet

from lametro.models import LAMetroBill, LAMetroEvent, LAMetroSubject
from lametro.smartlogic import SmartLogic


class SmartLogicAPI(ListView):
    api_key = settings.SMART_LOGIC_KEY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_to_response(self, context):
        '''
        Return response as JSON.
        '''
        try:
            return JsonResponse(context['object_list'])
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Could not retrieve SmartLogic token'
            }, status=500)

    def get_queryset(self, *args, **kwargs):
        '''
        Return a SmartLogic authentication token.
        '''
        return SmartLogic(settings.SMART_LOGIC_KEY).token()


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


def fetch_subjects(request):
    related_terms = request.GET.getlist('related_terms[]')
    subjects = list(LAMetroSubject.objects.filter(name__in=related_terms).values_list('name', flat=True))

    response = {
        'status_code': 200,
        'related_terms': related_terms,
        'subjects': subjects,
    }

    return JsonResponse(response)


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
