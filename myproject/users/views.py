from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views import generic

from .forms import UserRegistrationForm, UserLoginForm, EditProfileForm
from .models import Profile


def register_view(request):
    if(request.method == 'POST'):
        form = UserRegistrationForm(request.POST)
        if(form.is_valid()):
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created for {user.username}!")
            return redirect('index')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

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
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

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

    return render(request, 'edit_profile.html', {'form': profile_form})
"""
class EditProfilePageView(generic.UpdateView):
    model = Profile
    template_name = 'edit_profile.html'
    fields = ['avatar', 'linkedIn_username', 'linkedIn_password']
    success_url = '/'
"""