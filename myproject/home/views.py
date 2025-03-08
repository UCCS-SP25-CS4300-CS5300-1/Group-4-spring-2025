from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from users.models import Profile
from .forms import SearchJobForm


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'index.html', context)


@login_required
def dashboard(request):
    form = SearchJobForm()
    profile = Profile.objects.get(user=request.user)
    linkedIn_username = profile.linkedIn_username
    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']

    return render(request, 'dashboard.html', {'form': form, 'linkedIn_username': linkedIn_username})


def search_jobs():
    pass

