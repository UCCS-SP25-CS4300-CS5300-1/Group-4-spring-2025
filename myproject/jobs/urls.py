from django.urls import path
from .views import search_jobs

urlpatterns = [
    path('', search_jobs, name='search_jobs'),
]