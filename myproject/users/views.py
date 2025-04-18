from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views import generic
from pypdf import PdfReader
from docx2pdf import convert
from docx import Document
from django.http import FileResponse, Http404
import os
from django.utils.http import url_has_allowed_host_and_scheme

from jobs.models import Job
from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm, ResumeUploadForm, EditPreferenceForm
from .models import Profile, Resume
import os
import openai
import markdown

if(os.environ.get('OPENAI_API_KEY')):
    openai.api_key = os.environ.get('OPENAI_API_KEY')
else:
    openai.api_key = 'sk-proj-1234567890'
    
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
                if(not hasattr(user, 'profile')):
                    Profile.objects.create(user=user)
                
                login(request, user)
                
                messages.info(request, f"You are now logged in as {username}.")
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
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
    if(not hasattr(request.user, 'profile')):
        profile = Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile
        
    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, request.FILES, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, f"Your account has been updated.")
            return redirect('index')
    else:
        profile_form = EditProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': profile_form})

@login_required
def upload_resume(request):
    if(not hasattr(request.user, 'profile')):
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
            
            ## For DOCX files, we'll just save as is for now
            resume_instance.save()
            
            file = resume_instance.resume
            file_path = file.path

            try:
                text = parse_resume(file)
                    
                if request.user.is_superuser or profile.whitelisted_for_ai:
                    feedback = get_resume_feedback(text)
                    feedback_html = markdown.markdown(feedback)
                    return render(request, 'users/upload_resume.html', {
                        'form': resume_form, 
                        'feedback': feedback_html
                    })
                else:
                    return render(request, 'users/upload_resume.html', {
                        'form': resume_form,
                        'message': 'Resume uploaded successfully. AI feedback is only available to whitelisted users.'
                    })
            except Exception as e:
                import logging
                logger = logging.getLogger('users')
                logger.error(f"Error processing resume: {str(e)}")
                return render(request, 'users/upload_resume.html', {
                    'form': resume_form,
                    'message': 'Resume uploaded successfully, but there was an error processing it for feedback.'
                })
    else:
        resume_form = ResumeUploadForm()

    return render(request, 'users/upload_resume.html', {'form': resume_form})

def parse_resume(file):
    
    file_path = file.path
    filename = file.name.lower()
    
    if filename.endswith(".pdf"):
        reader = PdfReader(file)
        page = reader.pages[0]
        text = page.extract_text()
    elif filename.endswith(".docx"):
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        text = "Unsupported file type"
    
    return text

def get_resume_feedback(resume_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful resume reviewer. Review the following resume and provide constructive feedback. Focus on general advice, formatting, keyword optimization, and job relevance."},
                #{"role": "user", "content": f"Here are some helpful guidelines to follow when giving the feedback:\\n\\n"},
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
    if(not hasattr(request.user, 'profile')):
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
    """
    Display the user's preference selections
    """
    if(not hasattr(request.user, 'profile')):
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
            messages.success(request, f"Your preferences have been updated.")
            return redirect('index')
    else:
        profile_form = EditPreferenceForm(instance=profile)

    return render(request, 'users/update_preferences.html', {'form': profile_form})

@login_required
def view_resume(request, resume_id):
    """
    Securely serve resume files only to their owners
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    if(resume.user != request.user and not request.user.is_superuser):
        raise Http404("Resume not found")
    
    try:
        filename = resume.resume.name.lower()
        content_type = 'application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        response = FileResponse(open(resume.resume.path, 'rb'), content_type=content_type)
        
        ## Set content-disposition to inline for PDFs (view in browser) and attachment for DOCX (download)
        disposition = 'inline' if filename.endswith('.pdf') else 'attachment'
        response['Content-Disposition'] = f'{disposition}; filename="{os.path.basename(resume.resume.name)}"'
        
        return response
    except FileNotFoundError:
        raise Http404("Resume file not found")