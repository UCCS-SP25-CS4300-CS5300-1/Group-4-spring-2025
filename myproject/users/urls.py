from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('edit_profile/', views.update_user, name='edit_profile'),
    path('upload_resume/', views.upload_resume, name='upload_resume'),
    path('profile/', views.profile_view, name='profile'),
] 