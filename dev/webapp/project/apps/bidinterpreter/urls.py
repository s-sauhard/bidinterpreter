from django.urls import path
from django.conf.urls import url

from . import views
from . import views_bids
from . import views_deals
from .deal_views_downloads import DownloadCSV, DownloadPDF 
from .bid_import_wizard import ImportWizardView, test_json

app_name = "bidinterpreter"

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/users$', views.UserListView.as_view(), name='deal-users'),
    url(r'bids/$', views.BidListView.as_view(), name='bids'),
    url(r'deal/add/$', views_deals.DealCreate.as_view(), name='deal-add'),
    path('deal/<pk>/add_bid/',
         views.BidCreate.as_view(),
         kwargs={'bid_doc_id': None},
         name='bid-add'),
    url(r'bid/(?P<pk>[0-9]+)/update/$', views.BidUpdate.as_view(), name='bid-update'),
    url(r'bid/(?P<pk>[0-9]+)/delete/$', views.BidDelete.as_view(), name='bid-delete'),
    url(r'deal/(?P<pk>[0-9]+)/$', views_deals.DealUpdate.as_view(), name='deal-update'),
    url(r'deal/(?P<pk>[0-9]+)/delete/$', views_deals.DealDelete.as_view(), name='deal-delete'),
    url(r'deal/(?P<pk>[0-9]+)/import/(?P<doc_id>[0-9]+)$', ImportWizardView.as_view(), name='deal-import'),
    url(r'deal/(?P<deal_id>[0-9]+)/invite/(?P<pk>[0-9]+)/delete', views.DealInviteDelete.as_view(), name='invite-delete'),
    url(r'deal/test', test_json, name="json-test"),
    path(r'upload/', views.upload),
    url(r'deal/(?P<pk>[0-9]+)/upload/$', views.FileUploadView.as_view(), name="upload-document"),
    url(r'deal/(?P<pk>[0-9]+)/download/csv$', DownloadCSV.as_view(), name="download-csv"),
    url(r'deal/(?P<pk>[0-9]+)/download/pdf$', DownloadPDF.as_view(), name="download-pdf"),
    url(r'search/$', views.SearchView.as_view(),name = 'search'),
    url(r'search/json/$', views.JSONSearch.as_view(), name="search-json"),
    url(r'searchplugin/$', views.SearchPluginView.as_view(), name='searchplugin'),
    url(r'searchplugin/json/$', views.SearchPluginJSON, name="searchplugin-json"),
]
