from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from users.models import Profile
from home.models import Application
from .forms import SearchJobForm

# Selenium related
from selenium import webdriver
from selenium.webdriver.common.by import By

from applier_pilot.login import applier_pilot



def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'home/index.html', context)


@login_required
def dashboard(request):
    form = SearchJobForm()
    profile = Profile.objects.get(user=request.user)
    job_list = []
    #applications = Application.objects.filter(user=request.user)
    linkedIn_username = profile.linkedIn_username
    search_term = ''
    count = Application.objects.filter(user=request.user).count()
    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['search_term']
            job_list = applier_pilot(search_term, profile.linkedIn_username, profile.linkedIn_password, 25)


    return render(request, 'home/dashboard.html', {'form': form, 'linkedIn_username': linkedIn_username, 'job_list': job_list, 'search_term': search_term })


def search_jobs():
    pass

def login_linkedin(request):
    profile = Profile.objects.get(user=request.user)
    linkedIn_username = profile.linkedIn_username
    linkedIn_password = profile.linkedIn_password

    driver = webdriver.Firefox()
    driver.get("https://linkedin.com")
