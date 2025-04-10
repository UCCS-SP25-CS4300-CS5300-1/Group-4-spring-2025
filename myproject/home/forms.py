from django import forms
from django.core.exceptions import ValidationError

JOB_TYPE_CHOICES = [
    ('', 'Any Job Type'),
    ('Full-Time', 'Full-Time'),
    ('Part-Time', 'Part-Time'),
    ('Contract', 'Contract'),
]

class SearchJobForm(forms.Form):
    search_term = forms.CharField(
        max_length=100,
        required=False, # Allow searching with only filters
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter job title, skills or keywords...',
            'class': 'form-control'
        })
    )
    job_type = forms.ChoiceField(
        choices=JOB_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter location (e.g., USA, Remote)',
            'class': 'form-control'
        })
    )
    industry = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., IT, Finance, Healthcare',
            'class': 'form-control'
        })
    )
    job_level = forms.CharField( # Consider ChoiceField if levels are known
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Senior, Junior, Any',
            'class': 'form-control'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        search_term = cleaned_data.get('search_term')
        job_type = cleaned_data.get('job_type')
        location = cleaned_data.get('location')
        industry = cleaned_data.get('industry')
        job_level = cleaned_data.get('job_level')

        if(not (search_term or job_type or location or industry or job_level)):
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