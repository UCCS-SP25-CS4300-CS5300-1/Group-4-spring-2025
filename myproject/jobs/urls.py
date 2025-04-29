from django.urls import path
from .views import recommendations, search_jobs

urlpatterns = [
    path('recommendations/', recommendations, name='recommendations'),
    path('search/', search_jobs, name='search_jobs'),
]