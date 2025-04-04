from django.shortcuts import render
from .models import Job
from django.db.models import Q

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
    
    if salary_min or salary_max:
        try:
            min_val = int(salary_min) if salary_min else None
            max_val = int(salary_max) if salary_max else None
            
            if min_val is not None and min_val < 0:
                min_val = None
            if max_val is not None and max_val < 0:
                max_val = None
            if min_val is not None and max_val is not None and min_val > max_val:
                min_val = None
                max_val = None
            
            if min_val is not None and max_val is not None:
                jobs = jobs.filter(
                    salary_min__gte=min_val,
                    salary_min__lte=max_val
                )
            elif min_val is not None:
                jobs = jobs.filter(salary_min__gte=min_val)
            elif max_val is not None:
                jobs = jobs.filter(salary_max__lte=max_val)
                
        except ValueError:
            pass
    
    context = {'jobs': jobs}
    return render(request, 'jobs/job_list.html', context)