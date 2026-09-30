# personal/urls.py
from django.urls import path
from .views import DelegacionListView

urlpatterns = [
    path('delegaciones/', DelegacionListView.as_view(), name='delegacion_list'),
]