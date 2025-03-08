from django import forms


class SearchJobForm(forms.Form):
    search_term = forms.CharField(max_length=100)



