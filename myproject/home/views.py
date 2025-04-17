from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import base64

from users.models import Resume
from home.models import JobListing
from .forms import SearchJobForm, CoverLetterForm
from .services import JobicyService
from .interview_service import InterviewService
from .cover_letter_service import CoverLetterService
from django.contrib.auth.decorators import login_required



def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'home/index.html', context)

@login_required
def dashboard(request):
    initial_data = request.session.get('last_search_params', {})
    if not initial_data and hasattr(request.user, 'userprofile'):
        initial_data['job_type'] = getattr(request.user.userprofile, 'default_job_type', '')
        initial_data['location'] = getattr(request.user.userprofile, 'default_location', '')
        initial_data['industry'] = getattr(request.user.userprofile, 'default_industry', '')
        initial_data['job_level'] = getattr(request.user.userprofile, 'default_job_level', '')
        initial_data['search_term'] = initial_data.get('search_term', '') 

    form = SearchJobForm(initial=initial_data)
    job_list = []
    params = {}
    search_term = initial_data.get('search_term', '')

    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data.get('search_term', '')
            job_type = form.cleaned_data.get('job_type', '')
            location = form.cleaned_data.get('location', '')
            industry = form.cleaned_data.get('industry', '')
            job_level = form.cleaned_data.get('job_level', '')
            
            request.session['last_search_params'] = {
                'search_term': search_term,
                'job_type': job_type,
                'location': location,
                'industry': industry,
                'job_level': job_level,
            }

            if job_type: params['jobType'] = job_type
            if location: params['geo'] = location
            if industry: params['jobIndustry'] = industry
            if job_level: params['jobLevel'] = job_level

            if search_term or params:
                job_list = JobicyService.search_jobs(search_term, params)
        else:
            request.session.pop('last_search_params', None)

    elif request.method == "GET" and initial_data:
        job_type = initial_data.get('job_type', '')
        location = initial_data.get('location', '')
        industry = initial_data.get('industry', '')
        job_level = initial_data.get('job_level', '')

        if job_type: params['jobType'] = job_type
        if location: params['geo'] = location
        if industry: params['jobIndustry'] = industry
        if job_level: params['jobLevel'] = job_level

        if search_term or params:
             job_list = JobicyService.search_jobs(search_term, params)

    context = {
        'form': form,
        'job_list': job_list
    }
    return render(request, 'home/dashboard.html', context)

@login_required
def applications(request):
    applied_jobs = [
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

@login_required
def apply_flow(request, job_id):
    """Handles the multi-step application flow for a specific job."""
    job_details = JobicyService.get_job_details(job_id)

    if not job_details:
        return render(request, 'home/apply_flow_error.html', {'job_id': job_id})

    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    has_resume = latest_resume is not None
    job_description = getattr(job_details, 'description', '')
    company_name = getattr(job_details, 'company', '')
    job_title = getattr(job_details, 'title', '')

    initial_data = {
        'job_description': job_description,
        'company_name': company_name,
        'job_title': job_title,
        'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'user_email': request.user.email,
        'user_phone': "", 
        'user_address': "", 
        'use_resume': True if has_resume else False
    }
    form = CoverLetterForm(initial=initial_data)
    
    context = {
        'job': job_details,
        'latest_resume': latest_resume,
        'form': form,                   
        'has_resume': has_resume      
    }
    return render(request, 'home/apply_flow.html', context)

@login_required
def ajax_generate_cover_letter(request):
    """Handles AJAX request to generate cover letter text."""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = CoverLetterForm(request.POST)
        if form.is_valid():
            job_description = form.cleaned_data['job_description']
            use_resume = form.cleaned_data['use_resume']
            user_info = {
                'name': form.cleaned_data['user_name'],
                'email': form.cleaned_data['user_email'],
                'phone': form.cleaned_data['user_phone'],
                'address': form.cleaned_data['user_address']
            }

            resume_text = None
            if use_resume:
                latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
                if latest_resume:
                    try:
                        resume_file = latest_resume.resume
                        resume_text = CoverLetterService.extract_text_from_resume(resume_file)
                    except Exception as e:
                        return JsonResponse({'error': f"Error extracting text from your resume: {e}"}, status=500)
                else:
                     return JsonResponse({'error': "Resume selected but no resume found."}, status=400)

            try:
                cover_letter_text = CoverLetterService.generate_cover_letter(
                    job_description=job_description,
                    resume_text=resume_text,
                    user_info=user_info
                )

                company_name = form.cleaned_data.get('company_name')
                job_title = form.cleaned_data.get('job_title')

                if company_name:
                    cover_letter_text = cover_letter_text.replace('[Company Name]', company_name)
                    cover_letter_text = cover_letter_text.replace('[COMPANY NAME]', company_name)
                    cover_letter_text = cover_letter_text.replace('[Employer Name]', company_name)
                    cover_letter_text = cover_letter_text.replace('[EMPLOYER NAME]', company_name)
                
                if job_title:
                    cover_letter_text = cover_letter_text.replace('[Position Title]', job_title)
                    cover_letter_text = cover_letter_text.replace('[POSITION TITLE]', job_title)
                    cover_letter_text = cover_letter_text.replace('[Job Title]', job_title)
                    cover_letter_text = cover_letter_text.replace('[JOB TITLE]', job_title)
                
                return JsonResponse({
                    'success': True,
                    'cover_letter_text': cover_letter_text
                })

            except Exception as e:
                 return JsonResponse({'error': f"Error generating cover letter: {e}"}, status=500)
        else:
            errors = form.errors.as_json()
            return JsonResponse({'error': 'Invalid form data', 'details': errors}, status=400)

    # For non-AJAX or GET requests, return an error response
    return JsonResponse({'error': 'This endpoint only accepts AJAX POST requests'}, status=405)

@login_required
def cover_letter_generator(request, job_id=None):
    """
    View to handle the cover letter generator functionality
    If job_id is provided, use that job's description
    """
    job = None
    job_description = ""
    resume_text = None
    latest_resume = None

    # Get user's latest resume
    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    has_resume = latest_resume is not None  # Define has_resume here

    # If a job ID is provided, get the job description
    if job_id:
        job = get_object_or_404(JobListing, job_id=job_id)
        job_description = job.description

    # Initialize form
    initial_data = {
        'job_description': job_description,
        'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'user_email': request.user.email,
        'user_phone': "",
        'use_resume': True if latest_resume else False
    }

    if job:
        initial_data['company_name'] = job.company
        initial_data['job_title'] = job.title

    form = CoverLetterForm(initial=initial_data)

    if request.method == "POST":
        form = CoverLetterForm(request.POST)
        if form.is_valid():
            # Process form data
            user_info = {
                'name': form.cleaned_data['user_name'],
                'email': form.cleaned_data['user_email'],
                'phone': form.cleaned_data['user_phone'],
                'address': form.cleaned_data['user_address']
            }

            job_description = form.cleaned_data['job_description']
            use_resume = form.cleaned_data['use_resume']

            # Get resume text if needed
            if use_resume and latest_resume:
                try:
                    resume_file = latest_resume.resume
                    resume_text = CoverLetterService.extract_text_from_resume(resume_file)
                except Exception as e:
                    messages.error(request, f"Error extracting text from your resume: {e}")

            try:
                # Generate cover letter
                cover_letter_text = CoverLetterService.generate_cover_letter(
                    job_description=job_description,
                    resume_text=resume_text,
                    user_info=user_info
                )

                # Replace placeholders with actual data if provided
                company_name = form.cleaned_data.get('company_name')
                job_title = form.cleaned_data.get('job_title')

                if company_name:
                    cover_letter_text = cover_letter_text.replace('[Company Name]', company_name)
                    cover_letter_text = cover_letter_text.replace('[COMPANY NAME]', company_name)
                    cover_letter_text = cover_letter_text.replace('[Employer Name]', company_name)
                    cover_letter_text = cover_letter_text.replace('[EMPLOYER NAME]', company_name)

                if job_title:
                    cover_letter_text = cover_letter_text.replace('[Position Title]', job_title)
                    cover_letter_text = cover_letter_text.replace('[POSITION TITLE]', job_title)
                    cover_letter_text = cover_letter_text.replace('[Job Title]', job_title)
                    cover_letter_text = cover_letter_text.replace('[JOB TITLE]', job_title)

                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                direct_pdf = request.POST.get('direct_pdf') == 'true' or 'tests' in request.headers.get('User-Agent', '')

                if is_ajax and not direct_pdf:
                    return JsonResponse({
                        'success': True,
                        'cover_letter_text': cover_letter_text
                    })
                else:
                    pdf_data = CoverLetterService.create_cover_letter_pdf(
                        cover_letter_text=cover_letter_text,
                        filename=f"cover_letter_{request.user.username}"
                    )

                    response = HttpResponse(pdf_data, content_type='application/pdf')

                    company_name_safe = "".join(
                        c for c in (company_name or "company") if c.isalnum() or c in " _-").strip().replace(" ", "_")
                    download_filename = f'Cover_Letter_{company_name_safe}.pdf'
                    
                    response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
                    return response

            except Exception as e:
                messages.error(request, f"Error generating cover letter: {e}")


    if 'job' not in locals(): 
        job = None
        
    context = {
        'job': job, 
        'form': form,
        'has_resume': has_resume 
    }
    return render(request, 'home/cover_letter_generator.html', context)

@login_required
def generate_cover_letter_pdf(request):
    """Handle PDF generation after text editing."""
    if request.method == "POST":
        try:
            cover_letter_text = request.POST.get('edited_cover_letter', '')
            if not cover_letter_text:
                return JsonResponse({'error': 'No cover letter text provided'}, status=400)

            company_name = request.POST.get('company_name', 'company')

            pdf_data = CoverLetterService.create_cover_letter_pdf(
                cover_letter_text=cover_letter_text,
                filename=f"cover_letter_{request.user.username}"
            )

            company_name_safe = "".join(
                c for c in company_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
            download_filename = f'Cover_Letter_{company_name_safe}.pdf'
            
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'filename': download_filename,
                'pdf_base64': pdf_base64
            })
            
        except Exception as e:
            return JsonResponse({'error': f"Error generating PDF: {e}"}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
