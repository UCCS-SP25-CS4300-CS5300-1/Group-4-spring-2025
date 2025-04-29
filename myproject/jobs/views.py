
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

def search_jobs(request):
    industry = request.GET.get('industry')
    location = request.GET.get('location')
    remote = request.GET.get('remote')  # 'yes' or 'no'
    salary_min = request.GET.get('salary_min')
    salary_max = request.GET.get('salary_max')

    jobs = Job.objects.all()

    if industry:
        jobs = jobs.filter(industry__icontains=industry)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if remote:
        if remote.lower() == 'yes':
            jobs = jobs.filter(is_remote=True)
        elif remote.lower() == 'no':
            jobs = jobs.filter(is_remote=False)

    if salary_min or salary_max:
        try:
            min_val = int(salary_min) if salary_min else None
            max_val = int(salary_max) if salary_max else None

            if min_val is not None and min_val < 0:
                min_val = None
            if max_val is not None and max_val < 0:
                max_val = None
            if min_val is not None and max_val is not None and min_val > max_val:
                min_val = None
                max_val = None

            if min_val is not None and max_val is not None:
                jobs = jobs.filter(
                    salary_min__gte=min_val,
                    salary_min__lte=max_val
                )
            elif min_val is not None:
                jobs = jobs.filter(salary_min__gte=min_val)
            elif max_val is not None:
                jobs = jobs.filter(salary_max__lte=max_val)

        except ValueError:
            pass

    context = {'jobs': jobs}
    return render(request, 'jobs/job_list.html', context)
