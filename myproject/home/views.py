from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from home.models import JobListing
from .forms import SearchJobForm
from .services import JobicyService
from .interview_service import InterviewService


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'home/index.html', context)

@login_required
def dashboard(request):
    initial_data = {}

    if(hasattr(request.user, 'userprofile')):
        initial_data['job_type'] = getattr(request.user.userprofile, 'default_job_type', '')
        initial_data['location'] = getattr(request.user.userprofile, 'default_location', '')
        initial_data['industry'] = getattr(request.user.userprofile, 'default_industry', '')
        initial_data['job_level'] = getattr(request.user.userprofile, 'default_job_level', '')

    form = SearchJobForm(initial=initial_data)
    job_list = []
    params = {}

    if(request.method == "POST"):
        form = SearchJobForm(request.POST, initial=initial_data) # Keep initial data for redisplay
        if(form.is_valid()):
            search_term = form.cleaned_data.get('search_term', '')
            job_type = form.cleaned_data.get('job_type', '')
            location = form.cleaned_data.get('location', '')
            industry = form.cleaned_data.get('industry', '')
            job_level = form.cleaned_data.get('job_level', '')

            if(job_type):
                params['jobType'] = job_type
            if(location):
                params['geo'] = location
            if(industry):
                params['jobIndustry'] = industry
            if(job_level):
                params['jobLevel'] = job_level

            if(search_term or params):
                job_list = JobicyService.search_jobs(search_term, params)

    context = {
        'form': form,
        'job_list': job_list
    }
    return render(request, 'home/dashboard.html', context)

@login_required
def applications(request):
    applied_jobs = [ # mock data, replace this with logic
        {
            "job_id": 1, 
            "title": "Software Engineer", 
            "company": "Tesseract",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2024/04/ebafc0a3-221.jpeg",
            "job_type": "full_time",
            "location": "Richmond, VA",
            "description": "As a Software Engineer at Tesseract, you will be responsible for designing, developing, and maintaining software solutions that enhance the company's product offerings. You'll collaborate with cross-functional teams to implement scalable and efficient systems, ensuring high-performance and reliability. Your work will involve using modern programming languages and technologies to solve complex problems and improve user experiences.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "60000",
            "salary_max": "100000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Developer", 
            "company": "Midna",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/01/WRILS-210105054741-917528.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Engineer", 
            "company": "Jayce",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2022/02/f269bad3-221.jpeg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Computer Scientist", 
            "company": "MikeLabs",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/09/372fbf25d6bbb7ba24bc519fac29dbf9.jpeg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Consultant", 
            "company": "Bondrewdo",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/09/50cccf084c34089de2274f72e18841d0.jpg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "IT Specialist", 
            "company": "Jesnix",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2020/08/FNDL-200825111113-468175.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Sr. Software Developer", 
            "company": "Ardemi",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/10/ab5e97ed23587138329ff60a8dd8ad95.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
    ]
    viewed_jobs = [
        {
            "job_id": 3, 
            "title": "Cyber Analyst", 
            "company": "Oceanic",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/08/a0f68d769896c0f098621799a6396382.jpeg",
            "job_type": "full_time",
            "location": "Charlottesville, VA",
            "description": "Oceanic is looking for a skilled Cyber Analyst to protect the company's digital infrastructure. In this role, you will monitor, detect, and respond to cybersecurity threats, ensuring the integrity and security of systems. You will analyze security breaches, conduct vulnerability assessments, and collaborate with teams to implement robust security measures. Your expertise will play a vital role in safeguarding sensitive data and protecting the organization from cyberattacks.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "30000",
            "salary_max": "900000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 4, 
            "title": "Sr. Software Engineer", 
            "company": "Urasawa",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/04/Headspace.jpg",
            "job_type": "part_time",
            "location": "Los Angeles, CA",
            "description": "As a Senior Software Engineer at Urasawa, you will lead the development of high-quality software solutions that align with the company's strategic goals. You'll guide teams through technical challenges, design and architect software systems, and mentor junior engineers. Your role will involve using cutting-edge technologies to build scalable, secure, and maintainable solutions while ensuring performance optimization and code quality.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "80000",
            "salary_max": "120000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 1, 
            "title": "Software Engineer", 
            "company": "Tesseract",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2024/04/ebafc0a3-221.jpeg",
            "job_type": "full_time",
            "location": "Richmond, VA",
            "description": "As a Software Engineer at Tesseract, you will be responsible for designing, developing, and maintaining software solutions that enhance the company's product offerings. You'll collaborate with cross-functional teams to implement scalable and efficient systems, ensuring high-performance and reliability. Your work will involve using modern programming languages and technologies to solve complex problems and improve user experiences.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "60000",
            "salary_max": "100000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Developer", 
            "company": "Midna",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/01/WRILS-210105054741-917528.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Engineer", 
            "company": "Jayce",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2022/02/f269bad3-221.jpeg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Computer Scientist", 
            "company": "MikeLabs",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/09/372fbf25d6bbb7ba24bc519fac29dbf9.jpeg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Software Consultant", 
            "company": "Bondrewdo",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/09/50cccf084c34089de2274f72e18841d0.jpg",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "IT Specialist", 
            "company": "Jesnix",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2020/08/FNDL-200825111113-468175.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },
        {
            "job_id": 2, 
            "title": "Sr. Software Developer", 
            "company": "Ardemi",
            "company_logo": "https://jobicy.com/data/server-nyc0409/galaxy/mercury/2021/10/ab5e97ed23587138329ff60a8dd8ad95.png",
            "job_type": "part_time",
            "location": "Denver, CO",
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna's clients.",
            "url": "https://www.zeldaspeedruns.com/tp/",
            "salary_min": "70000",
            "salary_max": "110000",
            "salary_currency": "USD",
            "published_at": "2025-04-05",
            "created_at": "2025-04-05",
            "updated_at": "2025-04-05",
            "search_key": "computer science",
            "date": "2025-04-05",
        },        
    ]

    context = {
        'user': request.user,
        'applied_jobs': applied_jobs,
        'viewed_jobs': viewed_jobs
    }

    return render(request, 'home/applications.html', context)


@login_required
def interview_coach(request, job_id=None):
    """
    View to handle the interview coach functionality.
    Renders the page initially, questions are loaded via AJAX.
    """
    job = None
    job_description = ""

    if job_id:
        job = get_object_or_404(JobListing, job_id=job_id)
        job_description = job.description

    context = {
        'job': job,
        'job_description': job_description, 
        'questions': [],
    }
    return render(request, 'home/interview_coach.html', context)

@login_required
def ajax_generate_questions(request):
    """API endpoint to generate interview questions asynchronously."""
    if(request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        job_description = request.POST.get('job_description', '')
        
        try:
            questions = InterviewService.generate_interview_questions(job_description)
            return JsonResponse({'questions': questions})
        except Exception as e:
            return JsonResponse({'error': 'Failed to generate questions. Please try again.'}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def ajax_evaluate_response(request):
    """API endpoint to evaluate interview responses asynchronously"""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = request.POST
        question = data.get('question', '')
        response = data.get('response', '')
        job_description = data.get('job_description', '')

        # Validate input
        if not response:
            return JsonResponse({'error': 'Response is required'}, status=400)

        feedback = InterviewService.evaluate_response(question, response, job_description)
        return JsonResponse(feedback)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def search_jobs():
    """
    Placeholder function for legacy compatibility
    """
    pass