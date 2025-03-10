from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views import generic
from pypdf import PdfReader

from jobs.models import Job
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm, ResumeUploadForm
from .models import Profile, Resume


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
            message = f"The first 10 characters of the text from your resume is {text[:10]}"

            return render(request, 'users/upload_resume.html', {'form': resume_form, 'message': message})
    else:
        resume_form = ResumeUploadForm()

    return render(request, 'users/upload_resume.html', {'form': resume_form})

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