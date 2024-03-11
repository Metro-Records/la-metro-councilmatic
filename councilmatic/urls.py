from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views.static import serve
from django.views.decorators.cache import never_cache

from haystack.query import EmptySearchQuerySet

from councilmatic_core.views import (
    CouncilmaticSearchForm,
)
from councilmatic_core.feeds import CouncilmaticFacetedSearchFeed

from lametro.api import (
    PublicComment,
    refresh_guid_trigger,
    fetch_object_counts,
    LAMetroSmartLogicAPI,
)
from lametro.views import (
    LAMetroIndexView,
    LAMetroEventDetail,
    LABillDetail,
    LABoardMembersView,
    LAMetroAboutView,
    LACommitteeDetailView,
    LACommitteesView,
    LAPersonDetailView,
    LAMetroEventsView,
    LAMetroCouncilmaticFacetedSearchView,
    GoogleView,
    metro_login,
    metro_logout,
    delete_submission,
    delete_event,
    LAMetroArchiveSearch,
    LAMetroContactView,
    MinutesView,
    pong,
    test_logging,
    AlertDeleteView,
    AlertUpdateView,
)
from lametro.feeds import LAMetroPersonDetailFeed


patterns = (
    [
        url(
            r"^search/rss/",
            CouncilmaticFacetedSearchFeed(),
            name="councilmatic_search_feed",
        ),
        url(
            r"^search/",
            LAMetroCouncilmaticFacetedSearchView(
                searchqueryset=EmptySearchQuerySet, form_class=CouncilmaticSearchForm
            ),
            name="search",
        ),
        url(r"^archive-search", LAMetroArchiveSearch.as_view(), name="archive-search"),
        url(r"^$", never_cache(LAMetroIndexView.as_view()), name="index"),
        url(r"^about/$", LAMetroAboutView.as_view(), name="about"),
        url(
            r"^board-report/(?P<slug>[^/]+)/$",
            LABillDetail.as_view(),
            name="bill_detail",
        ),
        url(r"^committees/$", LACommitteesView.as_view(), name="committees"),
        url(
            r"^committee/(?P<slug>[^/]+)/$",
            LACommitteeDetailView.as_view(),
            name="committee",
        ),
        url(r"^board-members/$", LABoardMembersView.as_view(), name="council_members"),
        url(r"^person/(?P<slug>[^/]+)/$", LAPersonDetailView.as_view(), name="person"),
        url(
            r"^event/(?P<slug>[^/]+)/$",
            never_cache(LAMetroEventDetail.as_view()),
            name="events",
        ),
        url(r"^events/$", LAMetroEventsView.as_view(), name="event"),
        url(
            r"^person/(?P<slug>[^/]+)/rss/$",
            LAMetroPersonDetailFeed(),
            name="person_feed",
        ),
        url(
            r"^google66b34bb6957ad66c.html/$", GoogleView.as_view(), name="google_view"
        ),
        url(r"^public-comment/$", PublicComment.as_view(), name="public_comment"),
        url(r"^contact/$", LAMetroContactView.as_view(), name="contact"),
        url(r"^minutes/$", MinutesView.as_view(), name="minutes"),
    ],
    settings.APP_NAME,
)

urlpatterns = [
    url(r"", include(patterns)),
    url(r"^admin/", admin.site.urls),
    url(r"^metro-login/$", metro_login, name="metro_login"),
    url(r"^metro-logout/$", metro_logout, name="metro_logout"),
    url(r"^refresh-guid/(.*)$", refresh_guid_trigger, name="refresh_guid"),
    url(r"^object-counts/(.*)$", fetch_object_counts, name="object_counts"),
    url(
        r"^delete-submission/(?P<event_slug>[^/]+)/$",
        delete_submission,
        name="delete_submission",
    ),
    url(r"^delete-event/(?P<event_slug>[^/]+)/$", delete_event, name="delete_event"),
    path("alerts/<int:pk>/delete/", AlertDeleteView.as_view(), name="delete_alert"),
    path("alerts/<int:pk>/update/", AlertUpdateView.as_view(), name="update_alert"),
    url(
        r"^pong/$",
        pong,
    ),
    path(
        "smartlogic/concepts/<str:term>/<str:action>",
        LAMetroSmartLogicAPI.as_view(),
        name="lametro_ses_endpoint",
    ),
    path("smartlogic/", include("smartlogic.urls", namespace="smartlogic")),
    url(r"", include("councilmatic_core.urls")),
    url(r"^test-logging/$", test_logging, name="test_logging"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r"^static/(?P<path>.*)/$", serve),
        url(
            r"^images/(?P<path>.*)/$",
            serve,
            {"document_root": settings.STATIC_ROOT + "/images/"},
        ),
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]
