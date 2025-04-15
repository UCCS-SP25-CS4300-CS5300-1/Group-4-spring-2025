from django import forms

class SearchJobForm(forms.Form):
    search_term = forms.CharField(max_length=100)


class InterviewResponseForm(forms.Form):
    """Form for handling interview responses"""
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