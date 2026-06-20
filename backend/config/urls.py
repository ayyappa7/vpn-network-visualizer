from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/servers/', include('servers.urls')),
    path('api/graph/', include('graph.urls')),
]