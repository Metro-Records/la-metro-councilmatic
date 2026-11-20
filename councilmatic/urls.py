from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.decorators.cache import never_cache

from haystack.query import EmptySearchQuerySet

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

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
    LACommitteeDetailView,
    LACommitteesView,
    LAPersonDetailView,
    LAMetroEventsView,
    LAMetroCouncilmaticFacetedSearchView,
    GoogleView,
    metro_login,
    metro_logout,
    delete_event,
    manual_event_live_link,
    LAMetroArchiveSearch,
    LAMetroContactView,
    MinutesView,
    TagAnalyticsView,
    TranslationFilesView,
    pdfviewer,
    pong,
    test_logging,
)

patterns = (
    [
        re_path(
            r"^search/",
            LAMetroCouncilmaticFacetedSearchView(searchqueryset=EmptySearchQuerySet),
            name="search",
        ),
        re_path(
            r"^archive-search", LAMetroArchiveSearch.as_view(), name="archive-search"
        ),
        re_path(r"^$", never_cache(LAMetroIndexView.as_view()), name="index"),
        re_path(
            r"^board-report/(?P<slug>[^/]+)/$",
            LABillDetail.as_view(),
            name="bill_detail",
        ),
        re_path(r"^committees/$", LACommitteesView.as_view(), name="committees"),
        re_path(
            r"^committee/(?P<slug>[^/]+)/$",
            LACommitteeDetailView.as_view(),
            name="committee",
        ),
        re_path(
            r"^board-members/$", LABoardMembersView.as_view(), name="council_members"
        ),
        re_path(
            r"^person/(?P<slug>[^/]+)/$", LAPersonDetailView.as_view(), name="person"
        ),
        re_path(
            r"^event/(?P<slug>[^/]+)/$",
            never_cache(LAMetroEventDetail.as_view()),
            name="event",
        ),
        re_path(r"^events/$", LAMetroEventsView.as_view(), name="events"),
        re_path(
            r"^google66b34bb6957ad66c.html/$", GoogleView.as_view(), name="google_view"
        ),
        re_path(r"^public-comment/$", PublicComment.as_view(), name="public_comment"),
        re_path(r"^contact/$", LAMetroContactView.as_view(), name="contact"),
        re_path(r"^minutes/$", MinutesView.as_view(), name="minutes"),
        re_path(
            r"^generate-tag-analytics/$",
            TagAnalyticsView.as_view(),
            name="generate_tag_analytics",
        ),
    ],
    settings.APP_NAME,
)

urlpatterns = [
    re_path(r"", include(patterns)),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^metro-login/$", metro_login, name="metro_login"),
    re_path(r"^metro-logout/$", metro_logout, name="metro_logout"),
    re_path(r"^refresh-guid/(.*)$", refresh_guid_trigger, name="refresh_guid"),
    re_path(r"^object-counts/(.*)$", fetch_object_counts, name="object_counts"),
    re_path(
        r"^delete-event/(?P<event_slug>[^/]+)/$", delete_event, name="delete_event"
    ),
    re_path(
        r"^manual_event_link/(?P<event_slug>[^/]+)/$",
        manual_event_live_link,
        name="manual_event_live_link",
    ),
    re_path(
        r"^pong/$",
        pong,
    ),
    path(
        "smartlogic/concepts/<str:term>/<str:action>",
        LAMetroSmartLogicAPI.as_view(),
        name="lametro_ses_endpoint",
    ),
    path("smartlogic/", include("smartlogic.urls", namespace="smartlogic")),
    path(
        "api/translations/<str:document_id>/",
        TranslationFilesView.as_view(),
        name="translation",
    ),
    re_path(r"^pdfviewer/$", pdfviewer, name="pdfviewer"),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("", include(wagtail_urls)),
    re_path(r"^test-logging/$", test_logging, name="test_logging"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        re_path(r"^static/(?P<path>.*)/$", serve),
        re_path(
            r"^images/(?P<path>.*)/$",
            serve,
            {"document_root": settings.STATIC_ROOT + "/images/"},
        ),
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ]
