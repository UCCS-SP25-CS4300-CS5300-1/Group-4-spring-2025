from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from users.models import Profile
from home.models import Application
from .forms import SearchJobForm

from applier_pilot.login import applier_pilot

def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'index.html', context)


@login_required
def dashboard(request):
    form = SearchJobForm()
    profile = Profile.objects.get(user=request.user)
    # applications = Application.objects.filter(user=request.user)
    LI_username = profile.linkedIn_username
    LI_password = profile.linkedIn_password
    # count = Application.objects.filter(user=request.user).count()
    job_list = []
    amount_of_jobs = 50
    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            job_list = applier_pilot(search_term, LI_username, LI_password, amount_of_jobs)
    return render(request, 'dashboard.html', {'form': form, 'LI_username': LI_username, 'job_list': job_list })


def login_linkedin(request):
    profile = Profile.objects.get(user=request.user)
    linkedIn_username = profile.linkedIn_username
    linkedIn_password = profile.linkedIn_password
    #driver = webdriver.Firefox()
    #driver.get("https://linkedin.com")