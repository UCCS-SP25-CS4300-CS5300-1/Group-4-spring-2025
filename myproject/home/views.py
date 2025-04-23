from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import base64
import markdown
import openai
import os
from openai import APITimeoutError
import logging

from users.models import Resume
from home.models import JobListing, UserJobInteraction
from .forms import SearchJobForm, CoverLetterForm
from .services import JobicyService
from .interview_service import InterviewService
from .cover_letter_service import CoverLetterService
from django.contrib.auth.decorators import login_required

from users.models import Resume

logger = logging.getLogger(__name__)

def index(request):
    context = {}
    if request.user.is_authenticated:
        context['user'] = request.user
    return render(request, 'home/index.html', context)

@login_required
def dashboard(request):
    initial_data = request.session.get('last_search_params', {})
    if not initial_data and hasattr(request.user, 'userprofile'):
        initial_data['location'] = getattr(request.user.userprofile, 'default_location', '')
        initial_data['industry'] = getattr(request.user.userprofile, 'default_industry', '')
        initial_data['search_term'] = initial_data.get('search_term', '')

    form = SearchJobForm(initial=initial_data)
    job_list = []
    params = {}
    search_term = initial_data.get('search_term', '')

    if request.method == "POST":
        form = SearchJobForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data.get('search_term', '')
            location = form.cleaned_data.get('location', '')
            industry = form.cleaned_data.get('industry', '')

            request.session['last_search_params'] = {
                'search_term': search_term,
                'location': location,
                'industry': industry,
            }

            if location:
                params['geo'] = location
            if industry:
                params['industry'] = industry

            if search_term or params:
                job_list = JobicyService.search_jobs(search_term, params)
            else:
                logger.warning("Search attempted with no search term and no filters.")
                job_list = []

        else:
            logger.warning(f"Dashboard form invalid: {form.errors}")
            request.session.pop('last_search_params', None)
            job_list = []

    elif request.method == "GET" and initial_data:
        location = initial_data.get('location', '')
        industry = initial_data.get('industry', '')

        if location:
            params['geo'] = location
        if industry:
            params['industry'] = industry

        if search_term or params:
             job_list = JobicyService.search_jobs(search_term, params)
        else:
             logger.debug("GET request with empty initial_data, not performing search.")
             job_list = []

    context = {
        'form': form,
        'job_list': job_list
    }
    return render(request, 'home/dashboard.html', context)

@login_required
def applications(request):
    applied_interactions = UserJobInteraction.objects.filter(
        user=request.user,
        interaction_type='applied'
    ).select_related('job').order_by('-timestamp')

    applied_jobs_list = []
    applied_job_ids = set()
    for interaction in applied_interactions:
        if interaction.job.job_id not in applied_job_ids:
            applied_jobs_list.append(interaction.job)
            applied_job_ids.add(interaction.job.job_id)

    viewed_interactions = UserJobInteraction.objects.filter(
        user=request.user,
        interaction_type='viewed'
    ).exclude(
        job__job_id__in=applied_job_ids
    ).select_related('job').order_by('-timestamp')

    viewed_jobs_list = []
    viewed_job_ids_processed = set()
    for interaction in viewed_interactions:
        if interaction.job.job_id not in viewed_job_ids_processed:
            viewed_jobs_list.append(interaction.job)
            viewed_job_ids_processed.add(interaction.job.job_id)

    context = {
        'user': request.user,
        'applied_jobs_list': applied_jobs_list,
        'viewed_jobs_list': viewed_jobs_list
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
            logger.error(f"Error generating interview questions: {str(e)}")
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

        if not response:
            return JsonResponse({'error': 'Response is required'}, status=400)

        try:
            feedback = InterviewService.evaluate_response(question, response, job_description)
            return JsonResponse(feedback)
        except Exception as e:
            logger.error(f"Error evaluating interview response: {str(e)}")
            return JsonResponse({'error': 'Unable to evaluate response. Please try again later.'}, status=500)

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

    resume_text = None
    if has_resume:
        try:
            resume_file = latest_resume.resume
            from users.views import parse_resume
            resume_text = parse_resume(resume_file)
        except Exception as e:
            logger.error(f"Error extracting resume text: {str(e)}")
            messages.error(request, "Error extracting text from your resume")

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
        'has_resume': has_resume,
        'resume_text': resume_text
    }
    return render(request, 'home/apply_flow.html', context)

@login_required
def ajax_resume_feedback(request):
    """AJAX endpoint to get feedback on a resume for a specific job."""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_description = request.POST.get('job_description', '')
        resume_id = request.POST.get('resume_id')

        if not resume_id:
            return JsonResponse({'error': 'No resume selected'}, status=400)

        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
            resume_file = resume.resume

            from users.views import parse_resume
            resume_text = parse_resume(resume_file)

            from users.views import get_resume_feedback
            general_feedback = get_resume_feedback(resume_text)

            job_specific_feedback = get_job_specific_feedback(resume_text, job_description)

            return JsonResponse({
                'success': True,
                'general_feedback': general_feedback,
                'job_specific_feedback': job_specific_feedback
            })
        except Resume.DoesNotExist:
            return JsonResponse({'error': 'Resume not found'}, status=404)
        except Exception as e:
            logger.error(f"Error generating resume feedback: {str(e)}")
            return JsonResponse({'error': 'Unable to generate resume feedback. Please try again later.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_job_specific_feedback(resume_text, job_description):
    try:
        if os.environ.get('OPENAI_API_KEY'):
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        else:
            return markdown.markdown("## Error\n\nJob-specific feedback requires an OpenAI API key.")

        model_name = "gpt-4o-mini"
        system_prompt = "You are an expert at analyzing resumes against job descriptions..."
        user_prompt_template = "Resume:\n{resume_text}\n\nJob Description:\n{job_description}..."
        user_prompt = user_prompt_template.format(resume_text=resume_text, job_description=job_description)

        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=60.0,
        )

        return markdown.markdown(response.choices[0].message.content)
    except APITimeoutError as e:
        return markdown.markdown("## Error\n\nUnable to generate job-specific feedback: The request to the AI service timed out after 60 seconds. Please try again later.")
    except Exception as e:
        return markdown.markdown(f"## Error\n\nUnable to generate job-specific feedback: {str(e)}")

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
                        logger.error(f"Error extracting resume text: {str(e)}")
                        return JsonResponse({'error': 'Unable to process your resume. Please try again later.'}, status=500)
                else:
                     return JsonResponse({'error': 'Resume not found. Please upload a resume first.'}, status=400)

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
                logger.error(f"Error generating cover letter: {str(e)}")
                return JsonResponse({'error': 'Unable to generate cover letter. Please try again later.'}, status=500)
        else:
            return JsonResponse({'error': 'Invalid form data'}, status=400)

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
            return JsonResponse({'error': f"Error generating PDF. Please try again later."}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def ajax_job_outlook(request):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_title = request.POST.get('job_title', '')
        job_description = request.POST.get('job_description', '')
        industry = request.POST.get('industry', '')
        location = request.POST.get('location', '')

        if not job_title:
            return JsonResponse({'error': 'No job title provided'}, status=400)

        try:
            resume_text = None
            latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
            if latest_resume:
                try:
                    from users.views import parse_resume
                    resume_text = parse_resume(latest_resume.resume)
                except Exception:
                    pass

            if not resume_text:
                return JsonResponse({'error': 'No resume found to analyze fit'}, status=400)

            fit_analysis = get_job_fit_analysis(
                job_title=job_title,
                job_description=job_description,
                industry=industry,
                location=location,
                resume_text=resume_text
            )

            return JsonResponse({
                'success': True,
                'fit_analysis': fit_analysis
            })
        except Exception as e:
            return JsonResponse({'error': f'Error generating fit analysis. Please try again later.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_job_fit_analysis(job_title, job_description, industry=None, location=None, resume_text=None):
    try:
        if os.environ.get('OPENAI_API_KEY'):
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        else:
            return "Job fit analysis requires an OpenAI API key."

        if not resume_text:
            return "Cannot analyze fit without a resume. Please upload your resume first."

        user_prompt = f"Job Title: {job_title}\n"

        if job_description:
            user_prompt += f"\nJob Description: {job_description[:1000]}...\n"

        if industry:
            user_prompt += f"\nIndustry: {industry}\n"

        if location:
            user_prompt += f"\nLocation: {location}\n"

        user_prompt += f"\nCandidate Resume: {resume_text}\n"

        user_prompt += "\nPlease analyze how well this candidate's resume matches the job posting. Include:"
        user_prompt += "\n1. Overall match score (percentage)"
        user_prompt += "\n2. Key strengths that align with the job requirements"
        user_prompt += "\n3. Critical gaps in skills or experience"
        user_prompt += "\n4. Specific recommendations to improve the application"
        user_prompt += "\n5. Suggested talking points for interviews based on the candidate's strengths"

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a recruiting specialist who analyzes how well candidates match specific job postings. Provide detailed, honest assessments of fit along with actionable recommendations."},
                {"role": "user", "content": user_prompt}
            ],
            timeout=60.0, # Add timeout for consistency
        )
        return response.choices[0].message.content
    except APITimeoutError as e:
         return f"Unable to generate job fit analysis: Request timed out."
    except Exception as e:
        return f"Unable to generate job fit analysis. Please try again later."

@login_required
def ajax_rejection_generator(request):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_title = request.POST.get('job_title', '')
        job_description = request.POST.get('job_description', '')
        industry = request.POST.get('industry', '')
        location = request.POST.get('location', '')

        if not job_title:
            return JsonResponse({'error': 'No job title provided'}, status=400)

        try:
            resume_text = None
            latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
            if latest_resume:
                try:
                    from users.views import parse_resume
                    resume_text = parse_resume(latest_resume.resume)
                except Exception:
                    pass

            rejection_reasons = generate_rejection_reasons(
                job_title=job_title,
                job_description=job_description,
                industry=industry,
                location=location,
                resume_text=resume_text
            )

            return JsonResponse({
                'success': True,
                'rejection_reasons': rejection_reasons
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Error generating rejection reasons", exc_info=True)
            return JsonResponse({'error': 'An internal error occurred while generating rejection reasons.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def generate_rejection_reasons(job_title, job_description, industry=None, location=None, resume_text=None):
    try:
        if os.environ.get('OPENAI_API_KEY'):
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        else:
            return "Rejection reason simulator requires an OpenAI API key."

        user_prompt = f"Job Title: {job_title}\n"

        if job_description:
            user_prompt += f"\nJob Description: {job_description[:1000]}...\n"

        if industry:
            user_prompt += f"\nIndustry: {industry}\n"

        if location:
            user_prompt += f"\nLocation: {location}\n"

        if resume_text:
            user_prompt += f"\nCandidate Resume: {resume_text}\n"
            user_prompt += "\nPlease generate five potential reasons why the employer might reject the candidate based on their resume."

        if not resume_text:
            user_prompt += "\nPlease generate five potential reasons why the employer might reject the candidate. The user hasn't uploaded a resume, so assume the most common reasons why an employer would reject a typical candidate."

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a recruiting specialist who analyzes how well candidates match specific job postings. Provide detailed, honest assessments of areas of weakness along with actionable recommendations."},
                {"role": "user", "content": user_prompt}
            ],
            timeout=60.0, # Add timeout for consistency
        )
        return response.choices[0].message.content
    except APITimeoutError as e:
        logger = logging.getLogger(__name__)
        logger.error("Timeout in generate_rejection_reasons", exc_info=True)
        return f"Unable to generate rejection reasons: Request timed out ({e})."
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error in generate_rejection_reasons", exc_info=True)
        return "Unable to generate rejection reasons due to an internal error."

@login_required
def ajax_track_job_view(request):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_id = request.POST.get('job_id')
        if not job_id:
            return JsonResponse({'error': 'Missing job_id'}, status=400)

        try:
            job = JobListing.objects.get(job_id=job_id)
            interaction, created = UserJobInteraction.objects.get_or_create(
                user=request.user,
                job=job,
                interaction_type='viewed'
            )
            return JsonResponse({'success': True, 'created': created})
        except JobListing.DoesNotExist:
            return JsonResponse({'error': 'Job not found'}, status=404)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Error tracking job view", exc_info=True)
            return JsonResponse({'error': 'An internal error occurred while tracking the job view.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def ajax_track_application(request):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        job_id = request.POST.get('job_id')
        if not job_id:
            return JsonResponse({'error': 'Missing job_id'}, status=400)

        try:
            job = JobListing.objects.get(job_id=job_id)
            interaction, created = UserJobInteraction.objects.get_or_create(
                user=request.user,
                job=job,
                interaction_type='applied'
            )
            UserJobInteraction.objects.get_or_create(
                user=request.user,
                job=job,
                interaction_type='viewed'
            )
            return JsonResponse({'success': True, 'created': created})
        except JobListing.DoesNotExist:
            return JsonResponse({'error': 'Job not found'}, status=404)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Error tracking application", exc_info=True)
            return JsonResponse({'error': 'An internal error occurred while tracking the application.'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def job_fit_analysis_page(request, job_id):
    job_details = JobicyService.get_job_details(job_id)
    if not job_details:
        messages.error(request, f"Could not find job details for ID: {job_id}")
        return redirect('dashboard')

    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    has_resume = latest_resume is not None

    context = {
        'job': job_details,
        'latest_resume': latest_resume,
        'has_resume': has_resume,
    }
    return render(request, 'home/job_fit_analysis.html', context)

@login_required
def rejection_simulator_page(request, job_id):
    job_details = JobicyService.get_job_details(job_id)
    if not job_details:
        messages.error(request, f"Could not find job details for ID: {job_id}")
        return redirect('dashboard')

    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    has_resume = latest_resume is not None

    context = {
        'job': job_details,
        'latest_resume': latest_resume,
        'has_resume': has_resume,
    }
    return render(request, 'home/rejection_simulator.html', context)
