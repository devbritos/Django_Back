from django.urls import path
from . import views


app_name = 'configuration'


urlpatterns = [
    path('metas/',views.GoalListView.as_view(), name = 'goal_list'),
    path('metas/nueva/',views.GoalCreateView.as_view(), name = 'goal_create'),
    path('periodos/nuevo/',views.PeriodCreateView.as_view(), name = 'period_create')
]