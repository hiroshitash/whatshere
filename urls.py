from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import settings
import config
from views import PlaceListViewBaseHandler, HomeViewHandler, LoginViewHandler, LogoutViewHandler, StaleDataViewHandler

#import guppy
#from guppy.heapy import Remote
#Remote.on()

admin.autodiscover()

#import pdb; pdb.set_trace()

if config.FLAG_INDIVIDUAL_WEBSITE:
    urlpatterns = patterns('',
        # Examples:
        url(r'.*lmedia/(?P<path>.*)$', 'django.views.static.serve',  
            {'document_root': settings.MEDIA_ROOT}),

        url(r"^auth/login", LoginViewHandler.as_view()),
        url(r"^auth/logout", LogoutViewHandler.as_view()),
        url(r"^data/stale.+", StaleDataViewHandler.as_view()),

#        url(r"^$", HomeViewHandler.as_view()),
        url(r'^$', PlaceListViewBaseHandler.as_view(), {'document_root': settings.MEDIA_ROOT, 'paginate_by': config.NUM_ENTRY_PER_PAGE}),
        url(r'^view.py.+', PlaceListViewBaseHandler.as_view(), {'document_root': settings.MEDIA_ROOT, 'paginate_by': config.NUM_ENTRY_PER_PAGE}),
        url(r'^view.+', PlaceListViewBaseHandler.as_view(), {'document_root': settings.MEDIA_ROOT, 'paginate_by': config.NUM_ENTRY_PER_PAGE}),

       url(r'^close_html/', 'whatshere_prod.views.close'),
       url(r'^channel.html$', 'channel.index'),
       url(r'(.+\.html)$', direct_to_template),
       url(r'(.+\.tmpl)$', direct_to_template),
       url(r'(robots\.txt)$', direct_to_template),

        # Uncomment the next line to enable the admin:
        url(r'^admin/', include(admin.site.urls)),
    )
else:
    urlpatterns = patterns('',
        # Examples:
        url(r'.*lmedia/(?P<path>.*)$', 'django.views.static.serve',  
            {'document_root': settings.MEDIA_ROOT}),

        url(r'^view.py.+', PlaceListViewBaseHandler.as_view(), {'document_root': settings.MEDIA_ROOT, 'paginate_by': config.NUM_ENTRY_PER_PAGE}),
        url(r'^$', PlaceListViewBaseHandler.as_view(), {'document_root': settings.MEDIA_ROOT, 'paginate_by': config.NUM_ENTRY_PER_PAGE}),

        url(r'^close_html/', 'whatshere_prod.views.close'),
        url(r'^channel.html$', 'channel.index'),
        url(r'(.+\.html)$', direct_to_template),
        url(r'(.+\.tmpl)$', direct_to_template),
        url(r'(robots\.txt)$', direct_to_template),

        # Uncomment the next line to enable the admin:
        url(r'^admin/', include(admin.site.urls)),
    )
