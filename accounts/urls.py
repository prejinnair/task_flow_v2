from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.my_account, name=''),
    path('login/', views.login, name='login'),
    path('my-account/', views.my_account, name='my-account'),
    path('logout/', views.logout, name='logout'),
    path('manager-dashboard/', views.manager_dashboard, name='manager-dashboard'),
    path('developer-dashboard/', views.developer_dashboard, name='developer-dashboard'),
    path('qa-dashboard/', views.qa_dashboard, name='qa-dashboard'),
    path('guest-dashboard/', views.guest_dashboard, name='guest-dashboard'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset_password_validate/<uidb64>/<token>/', views.reset_password_validate, name='reset_password_validate'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('user-list/', views.user_list_view, name='user_list'),
    path('user-detail/<int:user_id>/', views.user_detail_view, name='user_detail')
]
