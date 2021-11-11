import json

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import ListView

from smartlogic.client import SmartLogic


class SmartLogicAPI(ListView):

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
        smartlogic = SmartLogic(
            settings.SMART_LOGIC_KEY,
            token=self.request.GET.get('token', None)
        )

        endpoint = self.kwargs['endpoint']

        if endpoint == 'token':
            return smartlogic.token()

        elif endpoint == 'terms':
            return smartlogic.terms(self.request.GET.dict())

        elif endpoint == 'concepts':
            return smartlogic.concepts(self.kwargs['term'], self.request.GET.dict())
