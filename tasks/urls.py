from django.urls import path
from . import views

app_name = 'tasks'
urlpatterns = [
    # Task CRUD
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/edit/', views.task_update, name='task_update'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:task_id>/complete/', views.mark_task_completed, name='mark_completed'),

    # Comment CRUD (handled inside task detail usually)
    path('<int:task_id>/comment/add/', views.add_comment, name='comment_create'),

    # Label CRUD
    path('labels/', views.label_list, name='label_list'),
    path('labels/create/', views.label_create, name='label_create'),
    # path('labels/<int:pk>/edit/', views.label_update, name='label_update'),
    # path('labels/<int:pk>/delete/', views.label_delete, name='label_delete'),

    # Test Case CRUD
    path('testcases/', views.test_case_list, name='test_case_list'),
    path('tasks/<int:task_id>/test-cases/', views.test_case_list_by_task, name='test_case_list_by_task'),

    path('testcases/create/<int:task_id>/', views.test_case_create, name='test_case_create'),
    path('testcases/<int:pk>/', views.test_case_detail, name='test_case_detail'),
    path('testcases/<int:pk>/edit/', views.test_case_update, name='test_case_update'),
    path('testcases/<int:pk>/delete/', views.test_case_delete, name='test_case_delete'),

    # Optional: GitHub Integration (placeholder)
    # path('<int:task_id>/github-sync/', views.github_sync, name='github_sync'),
]
