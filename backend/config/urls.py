from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from .views import serve_spa

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/servers/', include('servers.urls')),
    path('api/graph/', include('graph.urls')),
]

if hasattr(settings, 'FRONTEND_BUILD_DIR') and settings.FRONTEND_BUILD_DIR.exists():
    urlpatterns += [
        re_path(r'^(?!api/|admin/|ws/)(?P<path>.*)$', serve_spa),
    ]