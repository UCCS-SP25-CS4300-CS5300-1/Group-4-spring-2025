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
    username = forms.CharField(label='Username')
    
    class Meta:
        model = User
        fields = ('username', 'password')
        
    error_messages = {
        'invalid_login': 'Invalid username or password.',
        'inactive': 'This account is inactive.',
    }


class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = Profile
        fields = ()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if(self.instance and self.instance.user):
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            
    def save(self, commit=True):
        profile = super().save(commit=False)
        if(commit):
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            profile.user.save()
            profile.save()
        return profile

class EditPreferenceForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('industry_preference', 'location_preference', 'remote_preference', 'salary_min_preference')


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['resume']
            
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:          
            if resume.content_type not in  ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                raise ValidationError("The file must be in PDF or docx format.")
            
        return resume