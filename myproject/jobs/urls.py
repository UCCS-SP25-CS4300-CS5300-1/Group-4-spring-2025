from django.urls import path
from .views import search_jobs, recommendations

urlpatterns = [
    path('', search_jobs, name='search_jobs'),
    path('recommendations/', recommendations, name='recommendations'),
]