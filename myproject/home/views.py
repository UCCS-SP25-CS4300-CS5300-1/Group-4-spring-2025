from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from users.models import Profile
from home.models import JobListing
from .forms import SearchJobForm, InterviewResponseForm
from .services import JobicyService
from .interview_service import InterviewService


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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Oceanic is looking for a skilled Cyber Analyst to protect the company’s digital infrastructure. In this role, you will monitor, detect, and respond to cybersecurity threats, ensuring the integrity and security of systems. You will analyze security breaches, conduct vulnerability assessments, and collaborate with teams to implement robust security measures. Your expertise will play a vital role in safeguarding sensitive data and protecting the organization from cyberattacks.",
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
            "description": "As a Senior Software Engineer at Urasawa, you will lead the development of high-quality software solutions that align with the company’s strategic goals. You’ll guide teams through technical challenges, design and architect software systems, and mentor junior engineers. Your role will involve using cutting-edge technologies to build scalable, secure, and maintainable solutions while ensuring performance optimization and code quality.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
            "description": "Midna is seeking a Software Developer to join their dynamic team. In this role, you will be responsible for building, testing, and deploying software applications that meet the needs of the business. You will work closely with other developers and stakeholders to write clean, efficient code while maintaining system performance and security. Your contributions will directly impact the development of innovative solutions for Midna’s clients.",
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
    View to handle the interview coach functionality
    If job_id is provided, use that job's description for the interview
    Otherwise, use a generic interview
    """
    job = None
    job_description = ""

    # If a job ID is provided, get the job description
    if job_id:
        job = get_object_or_404(JobListing, job_id=job_id)
        job_description = job.description

    # Generate interview questions
    questions = InterviewService.generate_interview_questions(job_description)

    # Handle response form submission
    feedback = None
    form = InterviewResponseForm(initial={'job_description': job_description})

    if request.method == "POST":
        form = InterviewResponseForm(request.POST)
        if form.is_valid():
            question = form.cleaned_data['question']
            response = form.cleaned_data['response']
            job_desc = form.cleaned_data.get('job_description', '')

            # Get feedback on user's response
            feedback = InterviewService.evaluate_response(question, response, job_desc)

            messages.success(request, "Response evaluated successfully!")

    context = {
        'job': job,
        'questions': questions,
        'form': form,
        'feedback': feedback
    }
    return render(request, 'home/interview_coach.html', context)


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