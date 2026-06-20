from django.urls import path, include, re_path
from django.conf import settings
from .views import serve_spa

urlpatterns = [
    path('api/servers/', include('servers.urls')),
]

if hasattr(settings, 'FRONTEND_BUILD_DIR') and settings.FRONTEND_BUILD_DIR.exists():
    urlpatterns += [
        re_path(r'^(?!api/|ws/)(?P<path>.*)$', serve_spa),
    ]