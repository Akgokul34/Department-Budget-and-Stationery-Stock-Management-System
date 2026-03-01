from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('manage/departments/', views.manage_departments, name='manage_departments'),
    path('manage/users/', views.manage_users, name='manage_users'),
    path('manage/users/<int:user_id>/reset/', views.reset_password, name='reset_password'),
]
