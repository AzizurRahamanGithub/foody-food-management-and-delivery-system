from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static
from .views import home

def favicon(request):
    return HttpResponse(status=204)

# URL Patterns
urlpatterns = [
    path("", home),  
    re_path(r'^favicon.ico$', favicon), 
    path('admin/', admin.site.urls), 
    path('summernote/', include('django_summernote.urls')),
    path("tinymce/", include("tinymce.urls")),
    path('api/v1/', include([
        # path('schema-viewer/', include('schema_viewer.urls')),
        path('auth/', include('apps.auths.urls')),
        path('file/', include('apps.file_uploader.urls')),
        path('contacts/', include('apps.contacts.urls')),
        path('notification/', include('apps.notification.urls')),
        path('chat/', include('apps.chat.urls')),
        path('merchant/', include('apps.merchant.urls')),
        path('customer/', include('apps.customer.urls')),
        path('rider/', include('apps.rider.urls')),
        path('admin-panel/', include('apps.admin_panel.urls')),
    ])),
]

# Static files for development mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
