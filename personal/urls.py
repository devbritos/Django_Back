# personal/urls.py
from django.urls import path
from .views import DelegationListView

urlpatterns = [
    path('delegations/', DelegationListView.as_view(), name='delegation_list'),
]