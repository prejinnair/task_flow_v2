from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/edit/', views.project_update, name='project_update'),
    path('<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/assign-team/', views.assign_team_to_project, name='assign_team_to_project'),
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('teams/<int:pk>/edit/', views.team_update, name='team_update'),
    path('teams/<int:pk>/delete/', views.team_delete, name='team_delete'),
]
