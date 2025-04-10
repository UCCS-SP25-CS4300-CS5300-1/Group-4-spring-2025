from django import forms

class SearchJobForm(forms.Form):
    search_term = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter job title, skills or keywords...',
            'class': 'form-control'
        })
    )


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