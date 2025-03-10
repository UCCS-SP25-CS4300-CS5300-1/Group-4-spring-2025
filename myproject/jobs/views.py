from django.shortcuts import render
from .models import Job
# Create your views here.

def search_jobs(request):
    # Retrieving filter parameters from the GET request
    industry = request.GET.get('industry')
    location = request.GET.get('location')
    remote = request.GET.get('remote')  # 'yes' or 'no'
    salary_min = request.GET.get('salary_min')
    salary_max = request.GET.get('salary_max')
    
    # Starting with all jobs
    jobs = Job.objects.all()
    
    # Applying filters based on provided criteria
    if industry:
        jobs = jobs.filter(industry__icontains=industry)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if remote:
        if remote.lower() == 'yes':
            jobs = jobs.filter(is_remote=True)
        elif remote.lower() == 'no':
            jobs = jobs.filter(is_remote=False)
    if salary_min:
        jobs = jobs.filter(salary_min__gte=salary_min)
    if salary_max:
        jobs = jobs.filter(salary_max__lte=salary_max)
    
    context = {'jobs': jobs}
    return render(request, 'jobs/job_list.html', context)