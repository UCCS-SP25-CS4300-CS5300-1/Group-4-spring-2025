from django.shortcuts import render

from home.cover_letter_service import CoverLetterService
from .models import Job
from users.models import Resume
from django.db.models import Q


def get_job_ai_recommendation(user):
    """Get feedback comparing resume to job description."""
    try:
        import openai
        import os
        if os.environ.get('OPENAI_API_KEY'):
            openai.api_key = os.environ.get('OPENAI_API_KEY')
        else:
            return "Job-specific feedback requires an OpenAI API key."

        resume_text = None
        latest_resume = None
        latest_resume = Resume.objects.filter(user=user).order_by('-uploaded_at').first()
        has_resume = latest_resume is not None

        if has_resume:
            resume_text = CoverLetterService.extract_text_from_resume(latest_resume)

        user_content = ''
        if has_resume and resume_text:
            user_content = f"Resume: \n{resume_text}\n\nIndustry: \n{user.profile.industry_preference}\n\nSalary: \n{user.profile.salary_min_preference}\n"
        else:
            user_content = f"Industry: \n{user.profile.industry_preference}\n\nSalary: \n{user.profile.salary_min_preference}\n"
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an expert at giving career recommendations based a resume. If the resume has no text, base it strictly off of industry preference and salary expectations."},
                {"role": "user",
                 "content": f"\n{user_content}\nBased on this information, provide some career trajectories or jobs. List the relevant skills that require to perform at the career or job. Can you embed html into it without quotes?"}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Unable to generate job-specific feedback: {str(e)}"

def recommendations(request):
    user = request.user
    ai_response = get_job_ai_recommendation(user)
    context = {'ai_response': ai_response}
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