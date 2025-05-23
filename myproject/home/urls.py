"""
This file contains the urls for the home app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('interview-coach/', views.interview_coach, name='interview_coach'),
    path('interview-coach/<str:job_id>/',
         views.interview_coach, name='interview_coach_with_job'),
    path('rejection-simulator/<str:job_id>/',
         views.rejection_simulator_page, name='rejection_simulator'),
    path('api/evaluate-response/',
         views.ajax_evaluate_response, name='evaluate_response'),
    path('api/generate-questions/',
         views.ajax_generate_questions, name='generate_questions'),
    path('applications/', views.applications, name='applications'),
    path('apply/<str:job_id>/', views.apply_flow, name='apply_flow'),
    path('cover-letter/',
         views.cover_letter_generator, name='cover_letter_generator'),
    path('cover-letter/<str:job_id>/',
         views.cover_letter_generator, name='cover_letter_generator_with_job'),
    path('ajax/generate-cover-letter/',
         views.ajax_generate_cover_letter, name='ajax_generate_cover_letter'),
    path('generate-cover-letter-pdf/',
         views.generate_cover_letter_pdf, name='generate_cover_letter_pdf'),
    path('ajax/resume-feedback/',
         views.ajax_resume_feedback, name='resume_feedback'),
    path('ajax/job-outlook/',
         views.ajax_job_outlook, name='job_outlook'),
    path('ajax/rejection-generator/',
         views.ajax_rejection_generator, name='rejection_generator'),
    path('ajax/track-job-view/',
         views.ajax_track_job_view, name='track_job_view'),
    path('ajax/track-application/',
         views.ajax_track_application, name='track_application'),
    path('fit-analysis/<str:job_id>/',
         views.job_fit_analysis_page, name='job_fit_analysis'),
]
