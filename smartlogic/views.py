import json

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import ListView

from smartlogic.client import SmartLogic


class SmartLogicAPI(ListView):

    ALLOWED_PARAMETERS = {
        'stop_cm_after_stage',
        'maxResultCount',
        'FILTER=AT'
    }

    def setup(self, request, *args, **kwargs):
        '''
        Initialize an instance of the SmartLogic client.
        '''
        super().setup(request, *args, **kwargs)

        self.smartlogic = SmartLogic(
            settings.SMART_LOGIC_KEY,
            authorization=self.request.headers.get('Authorization', None)
        )

    def render_to_response(self, context):
        '''
        Return response as JSON.
        '''
        try:
            return JsonResponse(context['object_list'])
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Could not serialize object list: {}'.format(str(context['object_list']))
            }, status=500)

    def get_queryset(self, *args, **kwargs):
        endpoint = self.kwargs['endpoint']

        query_parameters = {
            k: v for k, v in self.request.GET.items()
            if k in self.ALLOWED_PARAMETERS
        }

        if endpoint == 'token':
            return self.smartlogic.token()

        elif endpoint == 'terms':
            return self.smartlogic.terms(query_parameters)

        elif endpoint == 'concepts':
            return self.smartlogic.concepts(self.kwargs['term'], query_parameters)
