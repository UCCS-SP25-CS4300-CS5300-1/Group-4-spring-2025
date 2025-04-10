from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from users.models import Profile
from home.models import JobListing
from .forms import SearchJobForm
from .services import JobicyService

def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'home/index.html', context)


@login_required
def dashboard(request):
    form = SearchJobForm()
    job_list = []
    
    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            job_list = JobicyService.search_jobs(search_term)

    context = {
        'form': form,
        'job_list': job_list
    }
    return render(request, 'home/dashboard.html', context)


def search_jobs():
    pass
