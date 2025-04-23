from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('edit_profile/', views.update_user, name='edit_profile'),
    path('upload_resume/', views.upload_resume, name='upload_resume'),
    path('delete_resume/', views.delete_resume, name='delete_resume'),
    path('resume/<int:resume_id>/', views.view_resume, name='view_resume'),
    path('resume/<int:resume_id>/feedback/', views.resume_feedback, name='resume_feedback'),
    path('profile/', views.profile_view, name='profile'),
    path('edit_preferences/', views.update_preferences, name='update_preferences'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url='/users/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),
]