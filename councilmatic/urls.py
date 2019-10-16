from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles import views as staticviews
from django.views.generic.base import RedirectView
from django.conf import settings
from django.views.decorators.cache import never_cache

from haystack.query import SearchQuerySet, EmptySearchQuerySet

from councilmatic_core.views import CouncilmaticSearchForm, CouncilmaticFacetedSearchView, EventDetailView
from councilmatic_core.feeds import CouncilmaticFacetedSearchFeed
from lametro.views import LAMetroIndexView, LAMetroEventDetail, LABillDetail, LABoardMembersView, \
    LAMetroAboutView, LACommitteeDetailView, LACommitteesView, LAPersonDetailView, \
    LAMetroEventsView, LAMetroCouncilmaticFacetedSearchView, GoogleView, \
    metro_login, metro_logout, delete_submission, LAMetroArchiveSearch, refresh_guid_trigger, \
    SmartLogicAPI, fetch_topic
from lametro.feeds import *

patterns = ([
    url(r'^search/rss/',
        CouncilmaticFacetedSearchFeed(), name='councilmatic_search_feed'),
    url(r'^search/', LAMetroCouncilmaticFacetedSearchView(searchqueryset=EmptySearchQuerySet,
                                                          form_class=CouncilmaticSearchForm),
                                                          name='search'),
    url(r'^archive-search', LAMetroArchiveSearch.as_view(), name='archive-search'),
    url(r'^$', never_cache(LAMetroIndexView.as_view()), name='index'),
    url(r'^about/$', LAMetroAboutView.as_view(), name='about'),
    url(r'^board-report/(?P<slug>[^/]+)/$', LABillDetail.as_view(), name='bill_detail'),
    url(r'^committees/$', LACommitteesView.as_view(), name='committees'),
    url(r'^committee/(?P<slug>[^/]+)/$', LACommitteeDetailView.as_view(), name='committee'),
    url(r'^board-members/$', LABoardMembersView.as_view(), name='council_members'),
    url(r'^person/(?P<slug>[^/]+)/$', LAPersonDetailView.as_view(), name='person'),
    url(r'^event/(?P<slug>[^/]+)/$', never_cache(LAMetroEventDetail.as_view()), name='events'),
    url(r'^events/$', LAMetroEventsView.as_view(), name='event'),
    url(r'^person/(?P<slug>[^/]+)/rss/$', LAMetroPersonDetailFeed(), name='person_feed'),
    url(r'^google66b34bb6957ad66c.html/$', GoogleView.as_view(), name='google_view'),
    url(r'^refresh-guid/(.*)$', refresh_guid_trigger, name='refresh_guid')
], settings.APP_NAME)

urlpatterns = [
    url(r'', include(patterns)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^metro-login/$', metro_login, name='metro_login'),
    url(r'^metro-logout/$', metro_logout, name='metro_logout'),
    url(r'^ses-token/$', SmartLogicAPI.as_view(), name='ses_token'),
    url(r'^topic/$', fetch_topic, name='topic'),
    url(r'^delete-submission/(?P<event_slug>[^/]+)/$', delete_submission, name='delete_submission'),
    url(r'', include('councilmatic_core.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
      url(r'^static/(?P<path>.*)/$', staticviews.serve),
      url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
