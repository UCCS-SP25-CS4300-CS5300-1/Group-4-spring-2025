"""
This file contains the forms for the users app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from users.models import Profile, Resume # pylint: disable=import-error


class UserRegistrationForm(UserCreationForm): # pylint: disable=too-many-ancestors
    """
    This class contains the form for user registration.
    """
    email = forms.EmailField(required=True)

    class Meta: # pylint: disable=too-few-public-methods
        """
        This class contains the meta data for the user registration form.
        """
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        """
        This function saves the user.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    """
    This class contains the form for user login.
    """
    username = forms.CharField(label='Username')

    class Meta: # pylint: disable=too-few-public-methods
        """
        This class contains the meta data for the user login form.
        """
        model = User
        fields = ('username', 'password')

    error_messages = {
        'invalid_login': 'Invalid username or password.',
        'inactive': 'This account is inactive.',
    }


class EditProfileForm(forms.ModelForm):
    """
    This class contains the form for editing the profile.
    """
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta: # pylint: disable=too-few-public-methods
        """
        This class contains the meta data for the edit profile form.
        """
        model = Profile
        fields = ()

    def __init__(self, *args, **kwargs):
        """
        This function initializes the form.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        """
        This function saves the profile.
        """
        profile = super().save(commit=False)
        if commit:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            profile.user.save()
            profile.save()
        return profile

class EditPreferenceForm(forms.ModelForm):
    """
    This class contains the form for editing the preferences.
    """
    class Meta: # pylint: disable=too-few-public-methods
        """
        This class contains the meta data for the edit preference form.
        """
        model = Profile
        fields = ('industry_preference',
                  'location_preference',
                  'remote_preference', 'salary_min_preference')


class ResumeUploadForm(forms.ModelForm):
    """
    This class contains the form for uploading the resume.
    """
    class Meta: # pylint: disable=too-few-public-methods
        """
        This class contains the meta data for the resume upload form.
        """
        model = Resume
        fields = ['resume']
        widgets = {
            'resume': forms.FileInput(attrs={
                'accept': '.pdf,.docx',
                'class': 'form-control'
            })
        }

    def clean_resume(self):
        """
        This function cleans the resume.
        """
        resume = self.cleaned_data.get('resume')
        if resume:
            ext = resume.name.lower().split('.')[-1]

            if ext not in ['pdf', 'docx']:
                raise ValidationError("Only PDF and DOCX files are allowed.")

            if resume.content_type not in [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]:
                raise ValidationError("Invalid file type. Only PDF and DOCX files are allowed.")

            if resume.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError("File size cannot exceed 5MB.")

        return resume
