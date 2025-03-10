from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from users.models import Profile, Resume


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if(commit):
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Email / Username')
    
    class Meta:
        model = User
        fields = ('username', 'password')


class EditProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('linkedIn_username', 'linkedIn_password')

    linkedIn_password = forms.CharField(max_length=32, widget=forms.PasswordInput)

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['resume']
            
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:          
            if resume.content_type != 'application/pdf':
                raise ValidationError("The file must be in PDF format.")
            
        return resume