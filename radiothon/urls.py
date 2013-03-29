from django.conf.urls import patterns, include, url
from django.conf.urls.defaults import *
from radiothon import views, ajax
from radiothon.views import PledgeDetail

from django.contrib import admin
from django.contrib.auth.decorators import login_required
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'radiothon.views.home', name='home'),
    url(r'^radiothon/$', views.MainView.as_view(), name = 'index'),
    url(r'^radiothon/pledge/$', views.rthon_pledge, name = 'pledge-form'),
    url(r'^radiothon/pledge/(?P<pk>\d+)/$', login_required(PledgeDetail.as_view(), login_url = '/radiothon/accounts/login'), name = 'pledge-detail'),
    url(r'^radiothon/premium/(?P<amount>\d+(\.\d{2})?)/$', ajax.ajax_get_premium_forms_at_amount),
    url(r'^radiothon/premium/availability/(?P<premium>\d+)/(?P<options>\w+(/\w+)*)/$', ajax.ajax_get_premium_availability),
    
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^radiothon/admin/', include(admin.site.urls)),
    url(r'^radiothon/accounts/', include('registration.urls')),
)
