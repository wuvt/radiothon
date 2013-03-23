from django.conf.urls import patterns, include, url
from radiothon import views, ajax
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'radiothon.views.home', name='home'),
    
    url(r'^radiothon/pledge/$', views.rthon_pledge),
    url(r'^radiothon/pledge/review/$', views.rthon_review),
    url(r'^radiothon/premium/(?P<amount>\d+(\.\d{2})?)/$', ajax.ajax_get_premium_forms_at_amount),
    url(r'^radiothon/premium/availability/(?P<premium>\d+)/(?P<options>\w+(/\w+)*)/$', ajax.ajax_get_premium_availability),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
