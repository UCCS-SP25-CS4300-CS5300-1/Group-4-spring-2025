
from .models import Job
from django.shortcuts import render, get_object_or_404, redirect
from home.forms import SearchJobForm
from home.services import JobicyService
from home.cover_letter_service import CoverLetterService
from users.models import Profile, Resume


def get_job_ai_recommendation(user):
    """Get feedback comparing resume to job description."""
    try:
        import openai
        from dotenv import load_dotenv

        import os
        load_dotenv()
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            return "Job-specific feedback requires an OpenAI API key."

        latest_resume = Resume.objects.filter(user=user).order_by('-uploaded_at').first()
        has_resume = latest_resume is not None


        if has_resume:
            resume_text = CoverLetterService.extract_text_from_resume(latest_resume)
            user_content = f"Resume: \n{resume_text}\n\nIndustry: \n{user.profile.industry_preference}\n\nSalary: \n{user.profile.salary_min_preference}\n"
        else:
            user_content = f"Industry: \n{user.profile.industry_preference}\n\nSalary: \n{user.profile.salary_min_preference}\n"


        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You output a single search term of one of a few words for a job based on the information submitted. The information is a resume or if there's no resume, just the industry and salary."},
                {"role": "user",
                 "content": f"\n{user_content}\n\nOutput just the search term. Don't output my name or anything else besides the search term."}
            ],
        )


        return response.choices[0].message.content
    except Exception as e:
        return f"Unable to generate job-specific feedback: {str(e)}"


def recommendations(request):
    user = request.user
    params = {}
    context = {}

    job_list = []
    latest_resume = Resume.objects.filter(user=user).order_by('-uploaded_at').first()

    if latest_resume is None and user.profile.industry_preference == '' and user.profile.salary_min_preference == '':
        no_information_provided_string = "We need more information about your skills and preferences. Please consider uploading a resume or updating your profile to include industry or salary"
        context = {'no_information:': no_information_provided_string}
    else:
        ai_response = get_job_ai_recommendation(user)
        job_list = JobicyService.search_jobs(ai_response, params)
        context = {'job_list': job_list}


    return render(request, 'jobs/ai_recommendations.html', context)