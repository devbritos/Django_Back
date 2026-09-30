# personal/urls.py
from django.urls import path
from .views import (
    DelegationListView,
    DelegationCreateView,
    DelegationUpdateView,
    DelegationDeleteView,
)

urlpatterns = [
    path('delegations/', DelegationListView.as_view(), name='delegation_list'),
    path('delegations/new/', DelegationCreateView.as_view(),name = 'delegation_create' ),
    path('delegations/<int:pk>/edit/',DelegationUpdateView.as_view(),name= 'delegation_update'),
    path('delegations/<int:pk>/delete',DelegationDeleteView.as_view(),name ='delegation_delete'),
    
]