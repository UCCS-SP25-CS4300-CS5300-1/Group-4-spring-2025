from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from pypdf import PdfReader
from docx import Document
from django.http import FileResponse, Http404
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings

from .forms import (UserRegistrationForm, UserLoginForm, EditProfileForm,
                    ResumeUploadForm, EditPreferenceForm)
from .models import Profile, Resume
import os
import openai
import markdown
from openai import APITimeoutError
RESUME_GUIDE_TEXT = None

if (os.environ.get('OPENAI_API_KEY')):
    openai.api_key = os.environ.get('OPENAI_API_KEY')
else:
    openai.api_key = 'sk-proj-1234567890'


def register_view(request):
    if (request.method == 'POST'):
        form = UserRegistrationForm(request.POST)
        if (form.is_valid()):
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created for {user.username}!")
            return redirect('profile')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if (request.method == 'POST'):
        form = UserLoginForm(request, data=request.POST)
        if (form.is_valid()):
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if (user is not None):
                if (not hasattr(user, 'profile')):
                    Profile.objects.create(user=user)

                login(request, user)

                messages.info(request, f"You are now logged in as {username}.")
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                        next_url, allowed_hosts=None):
                    return redirect(next_url)
                return redirect('profile')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('index')


@login_required
def update_user(request):
    if (not hasattr(request.user, 'profile')):
        profile = Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile

    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, request.FILES,
                                       instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your account has been updated.")
            return redirect('index')
    else:
        profile_form = EditProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': profile_form})


@login_required
def upload_resume(request):
    if (not hasattr(request.user, 'profile')):
        profile = Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile

    if request.method == 'POST':
        resume_form = ResumeUploadForm(request.POST, request.FILES)

        if resume_form.is_valid():
            resume_instance = resume_form.save(commit=False)
            resume_instance.user = request.user

            file = resume_instance.resume
            filename = file.name.lower()

            resume_instance.save()
            messages.success(request,
                             "Your resume has been uploaded successfully.")
            return redirect('profile')

    else:
        resume_form = ResumeUploadForm()

    return render(request, 'users/upload_resume.html', {
        'form': resume_form,
    })


@login_required
def delete_resume(request):
    try:
        resumes = Resume.objects.filter(user=request.user)
        for resume in resumes:
            resume.resume.delete()
            resume.delete()
        messages.info(request, "You have removed your resume.")
    except Resume.DoesNotExist:
        messages.error(request, "You don't have a resume to delete.")

    return redirect('profile')


def parse_resume(file):

    file_path = file.path
    filename = file.name.lower()

    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif filename.endswith(".docx"):
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            text = "Unsupported file type"
    except Exception as e:
        text = f"Error parsing file: {e}"

    return text.strip()


def load_resume_guide():
    global RESUME_GUIDE_TEXT

    if RESUME_GUIDE_TEXT is not None:
        return RESUME_GUIDE_TEXT

    guide_path = os.path.join(settings.BASE_DIR, 'mediafiles', 'References',
                              'UCCS_Resume_Guide.pdf')
    try:
        with open(guide_path, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        RESUME_GUIDE_TEXT = text.strip()
        return RESUME_GUIDE_TEXT
    except Exception as e:
        return f"Error loading resume guide: {e}"


def get_resume_feedback(resume_text):
    guide_text = load_resume_guide()
    if "Error loading resume guide:" in guide_text:
        return "Could not generate feedback due to a configuration issue (unable to load guide)."

    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return "Could not generate feedback: OpenAI API key not configured."

        openai.api_key = os.environ.get('OPENAI_API_KEY')
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful resume reviewer. Review the following resume and provide constructive feedback. Focus on general advice, formatting, keyword optimization, and job relevance."},
                {"role": "user", "content": f"Here are some helpful guidelines to follow when giving the feedback:\n\n{guide_text}"},
                {"role": "user", "content": f"Please review this resume:\n\n{resume_text}"}
            ],
            timeout=60.0,
        )
        return markdown.markdown(response.choices[0].message.content)
    except APITimeoutError as e:
        return markdown.markdown("## Error\n\nError generating AI feedback: The request to the AI service timed out after 60 seconds. This might be due to a long resume or temporary high load on the AI service. Please try again later.")
    except Exception as ex:
        return markdown.markdown(f"## Error\n\nError generating AI feedback: {ex}")


@login_required
def resume_feedback(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    profile = request.user.profile
    feedback_html = ""
    error_message = ""

    try:
        if not (request.user.is_superuser or profile.whitelisted_for_ai):
            error_message = markdown.markdown("## Eligibility\n\nYou are not currently eligible for AI feedback. Please contact support if you believe this is an error.")
        else:
            if resume.ai_feedback:
                feedback_html = resume.ai_feedback
            else:
                resume_text = parse_resume(resume.resume)
                if "Error parsing file:" in resume_text or "Unsupported file type" in resume_text:
                    error_message = markdown.markdown(f"## Error\n\nCould not parse resume file: {resume_text}")
                else:
                    feedback_html = get_resume_feedback(resume_text)
                    if feedback_html.startswith("## Error") or "Could not generate feedback" in feedback_html:
                        error_message = feedback_html
                        feedback_html = ""
                    else:
                        resume.ai_feedback = feedback_html
                        resume.save()

    except Exception as e:
        error_message = markdown.markdown(f"## Error\n\nAn unexpected server error occurred while generating feedback: {str(e)}")

    context = {
        'resume': resume,
        'feedback': feedback_html,
        'error_message': error_message
    }
    return render(request, 'users/feedback_page.html', context)


@login_required
def profile_view(request):
    if (not hasattr(request.user, 'profile')):
        profile = Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile

    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()

    context = {
        'user': request.user,
        'profile': profile,
        'latest_resume': latest_resume,
    }

    return render(request, 'users/profile.html', context)


@login_required
def update_preferences(request):
    if (not hasattr(request.user, 'profile')):
        profile = Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile

    if request.method == 'POST':
        profile_form = EditPreferenceForm(request.POST, instance=profile)

        if profile_form.is_valid():
            if 'remote_preference' in request.POST and request.POST['remote_preference'] == 'True':
                profile_form.instance.remote_preference = True

            if 'salary_min_preference' in request.POST and request.POST['salary_min_preference']:
                try:
                    profile_form.instance.salary_min_preference = int(request.POST['salary_min_preference'])
                except ValueError:
                    pass

            profile_form.save()
            messages.success(request, "Your preferences have been updated.")
            return redirect('index')
    else:
        profile_form = EditPreferenceForm(instance=profile)

    return render(request, 'users/update_preferences.html', {'form': profile_form})


@login_required
def view_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)

    if (resume.user != request.user and not request.user.is_superuser):
        raise Http404("Resume not found")

    try:
        filename = resume.resume.name.lower()
        content_type = 'application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response = FileResponse(open(resume.resume.path, 'rb'), content_type=content_type)

        disposition = 'inline' if filename.endswith('.pdf') else 'attachment'
        response['Content-Disposition'] = f'{disposition}; filename="{os.path.basename(resume.resume.name)}"'

        return response
    except FileNotFoundError:
        raise Http404("Resume file not found")