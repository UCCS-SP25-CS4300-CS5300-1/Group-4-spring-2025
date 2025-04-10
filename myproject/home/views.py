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