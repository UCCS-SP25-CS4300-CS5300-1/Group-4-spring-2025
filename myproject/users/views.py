from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views import generic
from pypdf import PdfReader

from jobs.models import Job
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm, ResumeUploadForm, EditPreferenceForm
from .models import Profile, Resume
import os
import openai
import markdown
openai.api_key = os.environ.get('OPENAI_API_KEY')

def register_view(request):
    if(request.method == 'POST'):
        form = UserRegistrationForm(request.POST)
        if(form.is_valid()):
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created for {user.username}!")
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if(request.method == 'POST'):
        form = UserLoginForm(request, data=request.POST)
        if(form.is_valid()):
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if(user is not None):
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                next_url = request.GET.get('next')
                if(next_url):
                    return redirect(next_url)
                return redirect('profile')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('index')

@login_required
def update_user(request):
    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, f"Your account has been updated.")
            return redirect('index')
    else:
        profile_form = EditProfileForm(instance=request.user.profile)

    return render(request, 'users/edit_profile.html', {'form': profile_form})

def upload_resume(request):
    if request.method == 'POST':
        resume_form = ResumeUploadForm(request.POST, request.FILES)

        if resume_form.is_valid():
            resume_instance = resume_form.save()
            file = resume_instance.resume

            reader = PdfReader(file)
            page = reader.pages[0]
            text = page.extract_text()
            feedback = get_resume_feedback(text)
            feedback_html = markdown.markdown(feedback)
            
            return render(request, 'users/upload_resume.html', {'form': resume_form, 'feedback': feedback_html})
    else:
        resume_form = ResumeUploadForm()

    return render(request, 'users/upload_resume.html', {'form': resume_form})

def get_resume_feedback(resume_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful resume reviewer. Review the following resume and provide constructive feedback. Focus on general advice, formatting, keyword optimization, and job relevance."},
                {"role": "user", "content": f"Please review this resume:\\n\\n{resume_text}"}
            ],
        )
        return response.choices[0].message.content
    except Exception as ex:
        return f"Error generating AI feedback: {ex}"

@login_required
def profile_view(request):
    """
    Display the user's profile information
    """
    latest_resume = Resume.objects.order_by('-uploaded_at').first()
    
    context = {
        'user': request.user,
        'profile': request.user.profile,
        'latest_resume': latest_resume,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def update_preferences(request):
    """
    Display the user's preference selections
    """
    if request.method == 'POST':
        profile_form = EditPreferenceForm(request.POST, instance=request.user.profile)

        if profile_form.is_valid():
            # Convert remote_preference to boolean if it's a string
            if 'remote_preference' in request.POST and request.POST['remote_preference'] == 'True':
                profile_form.instance.remote_preference = True
            
            # Ensure salary_min_preference is an integer
            if 'salary_min_preference' in request.POST and request.POST['salary_min_preference']:
                try:
                    profile_form.instance.salary_min_preference = int(request.POST['salary_min_preference'])
                except ValueError:
                    pass  # Will be caught by form validation
                
            profile_form.save()
            messages.success(request, f"Your preferences have been updated.")
            return redirect('index')
    else:
        profile_form = EditPreferenceForm(instance=request.user.profile)

    return render(request, 'users/update_preferences.html', {'form': profile_form})