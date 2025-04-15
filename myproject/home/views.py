from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from users.models import Profile, Resume
from home.models import JobListing
from .forms import SearchJobForm, InterviewResponseForm, CoverLetterForm
from .services import JobicyService
from .interview_service import InterviewService
from .cover_letter_service import CoverLetterService


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
                'email': form.cleanefrom django.contrib.auth.decorators
            import login_required
            from django.shortcuts import render, get_object_or_404
            from django.http import JsonResponse, HttpResponse, FileResponse
            from django.contrib import messages

            from users.models import Profile, Resume
            from home.models import JobListing
            from .forms import SearchJobForm, InterviewResponseForm, CoverLetterForm
            from .services import JobicyService
            from .interview_service import InterviewService
            from .cover_letter_service import CoverLetterService


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

                # Create PDF
                pdf_data = CoverLetterService.create_cover_letter_pdf(
                    cover_letter_text=cover_letter_text,
                    filename=f"cover_letter_{request.user.username}"
                )

                # Create response
                response = HttpResponse(pdf_data, content_type='application/pdf')
                company_name_safe = "".join(
                    c for c in (company_name or "company") if c.isalnum() or c in " _-").strip().replace(" ", "_")
                response['Content-Disposition'] = f'attachment; filename="Cover_Letter_{company_name_safe}.pdf"'
                return response

            except Exception as e:
                messages.error(request, f"Error generating cover letter: {e}")

    context = {
        'job': job,
        'form': form,
        'has_resume': latest_resume is not None
    }
    return render(request, 'home/cover_letter_generator.html', context)


def search_jobs():
    pass