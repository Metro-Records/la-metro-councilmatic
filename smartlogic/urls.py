from django.urls import path

from smartlogic import views


app_name = "smartlogic"
urlpatterns = [
    path("<str:endpoint>/", views.SmartLogicAPI.as_view(), name="ses_endpoint"),
    path(
        "<str:endpoint>/<str:term>", views.SmartLogicAPI.as_view(), name="ses_endpoint"
    ),
]
