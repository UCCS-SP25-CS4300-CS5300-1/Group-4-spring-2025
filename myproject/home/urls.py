from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('interview-coach/', views.interview_coach, name='interview_coach'),
    path('interview-coach/<str:job_id>/', views.interview_coach, name='interview_coach_with_job'),
    path('api/evaluate-response/', views.ajax_evaluate_response, name='evaluate_response'),
    path('cover-letter/', views.cover_letter_generator, name='cover_letter_generator'),
    path('cover-letter/<str:job_id>/', views.cover_letter_generator, name='cover_letter_generator_with_job'),
]