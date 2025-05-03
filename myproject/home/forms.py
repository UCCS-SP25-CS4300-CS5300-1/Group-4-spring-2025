"""
This file contains the forms for the home app.
"""

from django import forms
from django.core.exceptions import ValidationError

LOCATION_CHOICES = [
    ('', 'Any Location'),
    ('usa', 'United States'),
    ('canada', 'Canada'),
    ('uk', 'United Kingdom'),
    ('europe', 'Europe'),
    ('apac', 'Asia Pacific'),
    ('emea', 'EMEA'),
    ('latam', 'Latin America')
]

class SearchJobForm(forms.Form):
    """Form for searching jobs"""
    search_term = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter job title, skills or keywords...',
            'class': 'form-control'
        })
    )
    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., IT, Finance, Healthcare',
            'class': 'form-control'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        search_term = cleaned_data.get('search_term')
        location = cleaned_data.get('location')
        industry = cleaned_data.get('industry')

        if not any([search_term, location, industry]):
            raise ValidationError("Please enter a search term or select at least one filter.")

        return cleaned_data


class InterviewResponseForm(forms.Form):
    """handling interview responses"""
    question = forms.CharField(widget=forms.HiddenInput())
    response = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'class': 'form-control',
            'placeholder': 'Type your response here...'
        }),
        required=True
    )
    job_description = forms.CharField(widget=forms.HiddenInput(), required=False)

class CoverLetterForm(forms.Form):
    """Form for generating cover letters"""
    user_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    user_phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_address = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    use_resume = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    job_description = forms.CharField(widget=forms.HiddenInput(), required=True)
    company_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
