from django.urls import path
from .views import TopologyView

urlpatterns = [
    path('topology/', TopologyView.as_view(), name='topology'),
]