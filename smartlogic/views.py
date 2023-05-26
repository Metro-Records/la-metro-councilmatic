import json

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import ListView
from requests.exceptions import HTTPError, ConnectTimeout

from smartlogic.client import SmartLogic
from smartlogic.exceptions import (
    RequestFailed,
    RequestNotAuthenticated,
    AuthenticationFailed,
    ResponseNotSerializable,
)


class SmartLogicAPI(ListView):
    ALLOWED_PARAMETERS = {"stop_cm_after_stage", "maxResultCount", "FILTER"}

    def setup(self, request, *args, **kwargs):
        """
        Initialize an instance of the SmartLogic client.
        """
        super().setup(request, *args, **kwargs)

        self.smartlogic = SmartLogic(
            settings.SMART_LOGIC_KEY,
            authorization=self.request.headers.get("Authorization", None),
        )

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)

        except HTTPError as e:
            message = "Could not reach SmartLogic"
            reason = e.response.reason
            status_code = e.response.status_code

        except ConnectTimeout:
            message = "Could not reach SmartLogic"
            reason = "Read timeout"
            status_code = 504

        except (
            RequestFailed,
            RequestNotAuthenticated,
            AuthenticationFailed,
            ResponseNotSerializable,
        ) as e:
            message = e.message
            reason = getattr(e, "reason", "")
            status_code = e.status_code

        except Exception as e:
            message = "Unanticipated error"
            reason = str(e)
            status_code = 500

        return JsonResponse(
            {"status": "error", "message": message, "reason": reason},
            status=status_code,
        )

    def render_to_response(self, context):
        """
        Return response as JSON.
        """
        try:
            return JsonResponse(context["object_list"])
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Could not serialize object list: {str(context['object_list'])}",
                },
                status=500,
            )

    def get_queryset(self, *args, **kwargs):
        endpoint = self.kwargs["endpoint"]

        query_parameters = {
            k: v for k, v in self.request.GET.items() if k in self.ALLOWED_PARAMETERS
        }

        if endpoint == "token":
            return self.smartlogic.token()

        elif endpoint == "terms":
            return self.smartlogic.terms(query_parameters)

        elif endpoint == "concepts":
            return self.smartlogic.concepts(self.kwargs["term"], query_parameters)
